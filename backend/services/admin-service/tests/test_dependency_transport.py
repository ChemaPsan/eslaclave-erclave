import io
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request, error

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from erclave_common import transport
from erclave_common.config import Settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.middleware import CorrelationIdMiddleware


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    settings = Settings(_env_file=None, environment="local", auth_mode="demo")
    monkeypatch.setattr(transport, "get_settings", lambda: settings)


def test_remaining_budget_and_correlation_are_propagated_without_retry(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(transport.time, "monotonic", lambda: now[0])
    end = transport.deadline.set(110)
    cid = transport.correlation.set("web-test")
    calls = []

    @contextmanager
    def opener(call, timeout):
        calls.append((call, timeout))
        yield io.BytesIO(b'{"data":[]}')

    try:
        for elapsed in (0, 6):
            now[0] = 100 + elapsed
            req = request.Request("http://localhost:8006/v1/hr/workers/production-eligible")
            with transport.open_dependency(req, timeout=12, opener=opener) as res:
                assert json.loads(res.read()) == {"data": []}
        assert [timeout for _, timeout in calls] == [9.75, 3.75]
        assert calls[1][0].get_header("X-request-timeout-ms") == "3750"
        assert calls[0][0].get_header("X-correlation-id") == "web-test"
        now[0] = 110
        with pytest.raises(TimeoutError):
            with transport.open_dependency(req, timeout=12, opener=opener):
                pytest.fail("exhausted budget started I/O")
        assert len(calls) == 2
    finally:
        transport.deadline.reset(end)
        transport.correlation.reset(cid)


@contextmanager
def local_server(delay, *, drip=False, status=200):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            calls.append(self.path)
            self.send_response(status)
            if not drip:
                self.send_header("Content-Length", str(len(b'{"data":true}')))
            self.end_headers()
            try:
                if drip:
                    for _ in range(30):
                        self.wfile.write(b"x")
                        self.wfile.flush()
                        time.sleep(delay)
                else:
                    time.sleep(delay)
                    self.wfile.write(b'{"data":true}')
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield request.Request(f"http://127.0.0.1:{server.server_port}/synthetic", data=b"{}"), calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_observed_cold_start_delay_succeeds_once():
    with local_server(6.86) as (req, calls):
        with transport.open_dependency(req, timeout=12, opener=request.urlopen) as res:
            assert json.loads(res.read()) == {"data": True}
        assert calls == ["/synthetic"]


@pytest.mark.parametrize("drip", [False, True])
def test_slow_body_is_bounded_and_mutation_is_never_repeated(drip):
    with local_server(0.02 if drip else 0.2, drip=drip) as (req, calls):
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            with transport.open_dependency(req, timeout=0.08, opener=request.urlopen) as res:
                res.read()
        assert time.monotonic() - started < 0.5
        assert calls == ["/synthetic"]


def test_http_rejection_is_preserved_and_not_repeated():
    calls = []
    def opener(call, timeout):
        calls.append(call)
        raise error.HTTPError(call.full_url, 403, "Forbidden", {}, None)
    with pytest.raises(error.HTTPError) as caught:
        with transport.open_dependency(request.Request("http://localhost:8006/x"), timeout=12, opener=opener):
            pass
    assert caught.value.code == 403 and caught.value.dependency_service == "hr"
    assert len(calls) == 1


def test_middleware_context_does_not_leak_and_errors_expose_safe_dependency():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(ErclaveError, erclave_error_handler)

    @app.get("/inspect")
    def inspect():
        return {"correlation": transport.correlation.get(), "remaining": transport.remaining_seconds()}

    @app.get("/fail")
    def fail():
        try:
            err = TimeoutError("DO NOT EXPOSE token or URL")
            err.dependency_service = "hr"
            raise err
        except TimeoutError as exc:
            raise ErclaveError("hr_service_unavailable", "Unavailable", 503) from exc

    with TestClient(app) as client:
        first = client.get("/inspect", headers={"X-Correlation-Id": "web-one", "X-Request-Timeout-Ms": "1000"}).json()
        second = client.get("/inspect", headers={"X-Request-Timeout-Ms": "999999"}).json()
        assert first["correlation"] == "web-one" and 0 < first["remaining"] <= 1
        assert second["correlation"] != "web-one" and 1 < second["remaining"] <= 25
        response = client.get("/fail")
        assert response.status_code == 503
        assert response.json()["error"]["details"] == {"dependency_service": "hr"}
        assert "DO NOT EXPOSE" not in response.text
    assert transport.correlation.get() is None and transport.deadline.get() is None


@pytest.mark.parametrize("status", [403,503])
def test_error_body_is_bounded_and_status_preserved(status):
    with local_server(0.02, drip=True, status=status) as (req,calls):
        started=time.monotonic()
        with pytest.raises(error.HTTPError) as caught:
            with transport.open_dependency(req,timeout=0.08,opener=request.urlopen):
                pass
        assert caught.value.code==status
        assert caught.value.read()==b""
        assert time.monotonic()-started<0.2
        assert calls==["/synthetic"]
