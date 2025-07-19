from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from core.routes.v1.audit_log import router as AuditLogRouterV1
from core.routes.authentication import router as AuthenticationRouter
from core.routes.v1.tenant import router as TenantRouter
from core.database.base import async_get_db, create_tables, dispose_db
from core.config import logger

app = FastAPI(
    title="Audit log API", docs_url="/docs", version="0.0.1"
)

app.include_router(AuthenticationRouter, tags=["Authentication"], prefix="/api/v1/authen")
app.include_router(AuditLogRouterV1, tags=["Audit Log v1"], prefix="/api/v1/logs")
app.include_router(TenantRouter, tags=["Tenant v1"], prefix="/api/v1/tenants")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "This only template for API of Audit log API, please revise it before using."
    }

@app.on_event("startup")
async def startup():
    await create_tables()
    logger.info("Startup completed and tables created.")

async def shutdown_event():
    await dispose_db()
    logger.info("Disconnected database")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "PUT", "DELETE", "OPTION", "GET"],
    allow_headers=["*"],
)

