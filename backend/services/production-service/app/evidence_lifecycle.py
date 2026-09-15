import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from starlette.responses import JSONResponse


class EvidenceBodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope.get("method")!="POST" or "/service-evidence/" not in scope.get("path",""):
            return await self.app(scope,receive,send)
        chunks=[];size=0
        while True:
            message=await receive()
            if message["type"]=="http.disconnect":return
            size+=len(message.get("body",b""))
            if size>21*1024*1024:
                return await JSONResponse({"error":{"code":"service_evidence_file_too_large","message":"Attachment request exceeds limit."}},status_code=413)(scope,receive,send)
            chunks.append(message)
            if not message.get("more_body"):break
        async def bounded_receive():
            if chunks:return chunks.pop(0)
            return await receive()
        await self.app(scope,bounded_receive,send)


@asynccontextmanager
async def evidence_lifespan(app):
    async def cleanup():
        from .repositories import get_production_repository
        while True:
            try:
                repo=get_production_repository()
                while await asyncio.to_thread(repo.purge_service_evidence):pass
            except Exception:
                logging.getLogger(__name__).exception("Service evidence retention cleanup failed; retrying in one hour")
            await asyncio.sleep(3600)
    task=asyncio.create_task(cleanup())
    try:yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):await task
