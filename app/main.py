import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from botocore.exceptions import ClientError

from models import URLCreate, URLResponse, URLInfo
from database import save_url, get_url, increment_visit_count
from cache import get_cached_url, cache_url
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Production-grade URL shortener with DevSecOps pipeline",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.app_name}


@app.post("/shorten", response_model=URLResponse)
def shorten_url(payload: URLCreate):
    original_url = str(payload.original_url)
    custom_code = payload.custom_code

    try:
        item = save_url(original_url, custom_code)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=409,
                detail="Short code already exists. Try a different custom code."
            )
        logger.error(f"DynamoDB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    cache_url(item["short_code"], original_url)

    return URLResponse(
        short_code=item["short_code"],
        original_url=original_url,
        short_url=f"{settings.base_url}/{item['short_code']}",
        created_at=item["created_at"]
    )


@app.get("/{short_code}/info", response_model=URLInfo)
def get_url_info(short_code: str):
    item = get_url(short_code)
    if not item:
        raise HTTPException(status_code=404, detail="Short code not found")

    return URLInfo(
        short_code=short_code,
        original_url=item["original_url"],
        short_url=f"{settings.base_url}/{short_code}",
        visit_count=int(item.get("visit_count", 0)),
        created_at=item["created_at"]
    )


@app.get("/{short_code}")
def redirect_url(short_code: str):
    cached = get_cached_url(short_code)
    if cached:
        logger.info(f"Cache hit for {short_code}")
        increment_visit_count(short_code)
        return RedirectResponse(url=cached, status_code=301)

    item = get_url(short_code)
    if not item:
        raise HTTPException(status_code=404, detail="Short code not found")

    cache_url(short_code, item["original_url"])
    increment_visit_count(short_code)
    return RedirectResponse(url=item["original_url"], status_code=301)