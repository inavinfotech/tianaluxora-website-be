import httpx
import logging
from typing import Optional

import sys
import json

# Setup logger for the BFF microservice communication
logger = logging.getLogger("tiana-bff.http")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Prevent duplicate logging if root logger also ends up handling it
    logger.propagate = False


def format_headers(headers) -> str:
    return "\\n".join([f"    {k}: {v}" for k, v in headers.items()])

async def log_request(request: httpx.Request):
    headers = format_headers(request.headers)
    logger.info(
        f"\n⬆️  [OUTBOUND] {request.method} {request.url} \n\n"
        f"Headers :{headers}\n"
    )

async def log_response(response: httpx.Response):
    request = response.request
    try:
        headers = format_headers(response.headers)
        
        level = logger.error if response.status_code >= 400 else logger.info
        status_icon = "❌" if response.status_code >= 400 else "✅"
        
        level(
            f"\n⬇️  [INBOUND] {status_icon} {response.status_code} from {request.url.host} ({request.method} {request.url})\n\n"
            f"Headers :{headers}"
        )  
    except Exception as e:
        logger.error(f"Failed to log microservice response from {request.url.host}: {e}")

def get_async_client() -> httpx.AsyncClient:
    """
    Returns an httpx.AsyncClient with comprehensive logging configured via event hooks.
    This centralized client intercepts all requests and responses to microservices.
    """
    return httpx.AsyncClient(
        timeout=60.0,
        event_hooks={
            "request": [log_request],
            "response": [log_response]
        }
    )
 