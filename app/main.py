"""
Tianaluxora Website Backend API - Main FastAPI Entry Point.
BFF (Backend For Frontend) orchestrating requests to:
- User Portal (auth & profile management)
- Inventory Portal (products & stock)
- OMS / Order Portal (order lifecycle)
- Payment Portal (Razorpay checkout)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.middleware.logging import LoggingMiddleware
from app.clients.inventory_client import inventory_client
from app.clients.order_client import order_client
from app.clients.payment_client import payment_client
from app.clients.user_portal_client import user_portal_client
from app.clients.coupon_client import coupon_client
from app.api import auth, products, orders, payments, admin, coupons, webhooks

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tiana-bff")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — manages persistent HTTP client pools."""
    logger.info("Initializing Tianaluxora Website BFF connections...")
    yield
    logger.info("Closing microservice client HTTP connections...")
    await inventory_client.close()
    await order_client.close()
    await payment_client.close()
    await user_portal_client.close()
    await coupon_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Structured request timing logger
app.add_middleware(LoggingMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


# Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(coupons.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "healthy",
        "version": "2.0.0",
    }


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://tianaluxora.com/</loc><priority>1.0</priority></url>
    <url><loc>https://tianaluxora.com/shop</loc><priority>0.9</priority></url>
    <url><loc>https://tianaluxora.com/about</loc><priority>0.7</priority></url>
    <url><loc>https://tianaluxora.com/contact</loc><priority>0.7</priority></url>
</urlset>"""
    return Response(content=content, media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)