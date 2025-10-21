from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class EnvironmentVariables(BaseSettings):
    DEBUG: bool = False
    DATABASE_URL: str
    AUTH_SECRET_KEY: str
    AUTH_REFRESH_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


env = EnvironmentVariables.model_validate({})
