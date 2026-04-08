from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Bling API v3 (OAuth2)
    bling_client_id: str = ""
    bling_client_secret: str = ""
    bling_access_token: str = ""
    bling_refresh_token: str = ""
    bling_redirect_uri: str = "http://localhost:8000/bling/callback"

    # Mercado Livre API
    ml_client_id: str = ""
    ml_client_secret: str = ""
    ml_access_token: str = ""
    ml_refresh_token: str = ""
    ml_seller_id: str = ""

    # Dashboard Authentication
    dash_username: str = "admin"
    dash_password: str = "admin"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
