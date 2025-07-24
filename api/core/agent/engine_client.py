from openai import AsyncAzureOpenAI
from core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
)
import httpx

ENGINE = AZURE_OPENAI_DEPLOYMENT_NAME
HTTPX_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0, read=60.0, write=60.0, pool=90.0
    ),
    limits=httpx.Limits(
        max_keepalive_connections=50, max_connections=200
    ),
)
AZURE_CLIENT = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=ENGINE,
    http_client=HTTPX_CLIENT,
)
