"""One outbound attempt, bounded waits and request-scoped correlation.

The operation budget prevents starting further I/O after exhaustion; it does
not cancel a database commit or imply that a timed-out mutation rolled back.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import logging
import io
import http.client
import time
from urllib import request as urllib_request
from urllib.error import HTTPError
from urllib.parse import urlsplit

from .config import get_settings

deadline = ContextVar("erclave_deadline", default=None)
correlation = ContextVar("erclave_correlation", default=None)
logger = logging.getLogger(__name__)
_standard_urlopen = urllib_request.urlopen


class DeadlineHTTPResponse(http.client.HTTPResponse):
    def __init__(self, sock, *args, **kwargs):
        self.budget_socket = sock
        super().__init__(sock, *args, **kwargs)


class DeadlineHTTPConnection(http.client.HTTPConnection):
    response_class = DeadlineHTTPResponse


class DeadlineHTTPSConnection(http.client.HTTPSConnection):
    response_class = DeadlineHTTPResponse


class DeadlineHTTPHandler(urllib_request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(DeadlineHTTPConnection, req)


class DeadlineHTTPSHandler(urllib_request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(DeadlineHTTPSConnection, req, context=self._context)


def _open_once(call, timeout):
    # Standard TLS verification and proxy support, with socket ownership kept
    # by our response class so each body read can use the remaining budget.
    return urllib_request.build_opener(DeadlineHTTPHandler(), DeadlineHTTPSHandler()).open(call, timeout=timeout)


def remaining_seconds():
    end = deadline.get()
    return None if end is None else max(0.0, end - time.monotonic())


def dependency_name(url):
    settings = get_settings()
    origin = urlsplit(url)
    for name in ("admin", "hr", "inventory", "production", "maintenance"):
        base = urlsplit(getattr(settings, name + "_service_url"))
        if (origin.scheme, origin.netloc) == (base.scheme, base.netloc):
            return name
    return "external"


class BudgetResponse:
    def __init__(self, response, end):
        self.response, self.end = response, end

    def read(self, size=-1):
        if time.monotonic() >= self.end:
            raise TimeoutError("Dependency response budget exhausted")
        # read1 returns after a socket read, so a slow trickle cannot keep a
        # read-to-EOF alive indefinitely. Each socket wait is also bounded.
        read1 = getattr(self.response, "read1", None)
        if read1 is None:
            data = self.response.read() if size < 0 else self.response.read(size)
            if time.monotonic() >= self.end:
                raise TimeoutError("Dependency response budget exhausted")
            return data
        chunks, length = [], 0
        while size < 0 or length < size:
            remaining = self.end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Dependency response budget exhausted")
            response = self.response.fp if isinstance(self.response, HTTPError) else self.response
            if getattr(response, "isclosed", lambda: False)():
                break
            sock = getattr(response, "budget_socket", None)
            if sock is not None:
                sock.settimeout(remaining)
            chunk = read1(65536 if size < 0 else min(65536, size - length))
            if time.monotonic() >= self.end:
                raise TimeoutError("Dependency response budget exhausted")
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        return b"".join(chunks)

    def __getattr__(self, name):
        return getattr(self.response, name)


@contextmanager
def open_dependency(call, *, timeout, opener):
    """Preserve urllib HTTP errors for existing domain error mapping. No retry."""
    remaining = remaining_seconds()
    # Reserve time for returning a structured error to the caller.
    allowed = float(timeout) if remaining is None else min(float(timeout), remaining - 0.25)
    if allowed <= 0:
        raise TimeoutError("Operation budget exhausted before dependency call")
    name = dependency_name(call.full_url)
    if name != "external":
        if correlation.get():
            call.add_header("X-Correlation-Id", correlation.get())
        call.add_header("X-Request-Timeout-Ms", str(max(1, int(allowed * 1000))))
    started = time.monotonic()
    outcome = "error"
    try:
        send = _open_once if opener is _standard_urlopen else opener
        with send(call, timeout=allowed) as response:
            yield BudgetResponse(response, started + allowed)
            outcome = "ok"
    except Exception as exc:
        # Safe diagnostic only; never retain URL, query string, token or body.
        if isinstance(exc, HTTPError):
            # Domain clients read error bodies too. Buffer them under the same
            # budget, then expose an in-memory stream preserving HTTP status.
            try:
                body = BudgetResponse(exc, started + allowed).read(65536)
            except (TimeoutError, OSError):
                body = b""
            finally:
                exc.close()
            buffered = HTTPError(exc.url, exc.code, exc.reason, exc.headers, io.BytesIO(body))
            buffered.dependency_service = name
            raise buffered from exc
        exc.dependency_service = name
        raise
    finally:
        # Local diagnostics only: no new Cloud Logging ingestion on deployment.
        if get_settings().environment == "local":
            logger.info("dependency service=%s method=%s duration_ms=%d outcome=%s correlation=%s",
                        name, call.get_method(), int((time.monotonic() - started) * 1000),
                        outcome, correlation.get() or "none")
