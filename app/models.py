from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None


class URLResponse(BaseModel):
    short_code: str
    original_url: str
    shorten_url: str
    created_at: str


class URLInfo(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    visit_count: int
    created_at: str