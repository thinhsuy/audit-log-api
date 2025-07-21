from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from core.routes.v1.audit_log import router as AuditLogRouterV1
from core.routes.authentication import router as AuthenticationRouter
from core.routes.v1.tenant import router as TenantRouter
from core.config import logger
from contextlib import asynccontextmanager
from core.database import init_db, get_engine, get_sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Establish engine and db session when startup API firstime
    then attach them into state
    """
    engine = get_engine()
    app.state.db_engine = engine
    app.state.db_sessionmaker = get_sessionmaker(engine)

    await init_db(engine)
    logger.info("Startup completed and tables created.")

    yield

    await engine.dispose()
    logger.info("Disconnected database")

app = FastAPI(
    title="Audit log API", docs_url="/docs", version="0.0.1",
    lifespan=lifespan
)

app.include_router(AuthenticationRouter, tags=["Authentication"], prefix="/api/v1/authen")
app.include_router(AuditLogRouterV1, tags=["Audit Log v1"], prefix="/api/v1/logs")
app.include_router(TenantRouter, tags=["Tenant v1"], prefix="/api/v1/tenants")

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

