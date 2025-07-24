from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from core.routes.v1.chatbot import router as ChatbotRouter
from core.routes.v1.audit_log import router as AuditLogRouterV1
from core.routes.authentication import router as AuthenticationRouter
from core.routes.v1.tenant import router as TenantRouter
from core.routes.v1.audit_log_ws import router as WsRouter
from core.config import logger
from contextlib import asynccontextmanager
from core.database import init_db, get_engine, get_sessionmaker
import asyncio
from core.services.bg_workers import BackgroundWorkers
from core.limiter import RATE_LIMITER
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Establish engine and db session when startup API firstime
    then attach them into state
    """
    engine = get_engine()
    app.state.db_engine = engine
    sessionmaker = get_sessionmaker(engine)
    app.state.db_sessionmaker = sessionmaker

    app.state._bg_workers_task = asyncio.create_task(
        BackgroundWorkers(sessionmaker).worker_loop()
    )

    await init_db(engine)
    logger.info("Startup completed and tables created.")

    yield

    app.state._bg_workers_task.cancel()
    await engine.dispose()
    logger.info("Disconnected database")


app = FastAPI(
    title="Audit log API",
    docs_url="/docs",
    version="0.0.1",
    lifespan=lifespan,
)

# config rate limiter
app.state.limiter = RATE_LIMITER.get_limiter()
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler
)
app.add_middleware(SlowAPIMiddleware)

app.include_router(
    AuthenticationRouter,
    tags=["Authentication"],
    prefix="/api/v1/authen",
)
app.include_router(
    AuditLogRouterV1,
    tags=["Audit Log v1"],
    prefix="/api/v1/logs",
)
app.include_router(
    TenantRouter,
    tags=["Tenant v1"],
    prefix="/api/v1/tenants",
)
app.include_router(
    ChatbotRouter,
    tags=["Chatbot v1"],
)
app.include_router(
    WsRouter, tags=["Websocket Audit Log v1"], prefix="/api/v1/logs"
)


@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Develop a comprehensive audit logging API system that tracks and manages user actions across different applications. This system should be designed to handle high-volume logging, provide search and filtering capabilities, and ensure data integrity and security."
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "PUT", "DELETE", "OPTION", "GET"],
    allow_headers=["*"],
)
