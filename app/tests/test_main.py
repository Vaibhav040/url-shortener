import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

# ------- Health Check -------

def test_health_check():
    response = client.get("/health")
    assert response.status_code==200
    assert response.json()["status"] == "healthy"


# ------- Shortern Url ------

@patch("app.main.save_url")
@patch("app.main.cache_url")

def test_shorten_url_success(mock_cache, mock_save):
    mock_save.return_value = {
        "short_code" : "abc1234",
        "original_url" : "https://google.com",
        "visist_count" : 0,
        "created_at" : "2026-01-01T00:00:00"
    }

    response = client.post("/shorten", json={
        "original_url": "https://google.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "abc1234"
    assert "shorten_url" in data
    mock_save.assert_called_once()
    mock_cache.assert_called_once()

@patch("app.main.save_url")
def test_shorten_url_duplicate_code(mock_save):
    from botocore.exceptions import ClientError
    mock_save.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException"}},
        "PutItem"
    )

    response = client.post("/shorten", json={
        "original_url" : "https://googl.com",
        "cutome_code" : "taken"
    })

    assert response.status_code == 409

def test_shorten_invalid_url():
    response = client.post("/shorten", json= {
        "original_url" : "not-a-real-url"
    })

    assert response.status_code == 422

# ------- Redirect -------

@patch("app.main.get_cached_url")
@patch("app.main.increment_visit_count")
def test_redirect_cache_hit(mock_increment, mock_cache):
    mock_cache.return_value = "https://google.com"

    response = client.get("/abc1234", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == "https://google.com"
    mock_increment.assert_called_once_with("abc1234")

@patch("app.main.get_cached_url")
@patch("app.main.get_url")
@patch("app.main.cache_url")
@patch("app.main.increment_visit_count")
def test_redirect_cache_miss(mock_increment, mock_cache, mock_get, mock_cached):
    mock_cached.return_value = None
    mock_get.return_value = {
        "short_code": "abc1234",
        "original_url": "https://google.com",
        "visit_count": 0,
        "created_at": "2026-01-01T00:00:00"
    }

    response = client.get("/abc1234", follow_redirects=False)

    assert response.status_code == 301
    mock_cache.assert_called_once()
    mock_increment.assert_called_once()

@patch("app.main.get_cached_url")
@patch("app.main.get_url")
def test_redirect_not_found(mock_get, mock_cached):
    mock_cached.return_value = None
    mock_get.return_value = None

    response = client.get("/nonexistent", follow_redirects=False)

    assert response.status_code == 404

# ------- URL Info -------

@patch("app.main.get_url")
def test_get_url_info(mocke_get):
    mocke_get.return_value = {
        "short_code": "abc1234",
        "original_url": "https://google.com",
        "visit_count": 5,
        "created_at": "2026-01-01T00:00:00"
    }

    response = client.get("/abc1234/info")

    assert response.status_code == 200
    data = response.json()
    assert data["visit_count"] == 5
    assert data["short_code"] == "abc1234"

@patch("app.main.get_url")
def test_get_url_info_not_found(mock_get):
    mock_get.return_value = None

    response =client.get("/nonexistent/info")

    assert response.status_code == 404