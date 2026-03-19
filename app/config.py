from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "URL Shortener"
    base_url: str = "http://localhost:8000"
    aws_region: str = "ap-south-1"
    dynamo_table: str = "url-shortener"
    redis_host: str = "localhost"
    redis_port: int = 6379
    short_code_length: int = 7

    class config:
        env_file = ".env"

Settings = Settings()