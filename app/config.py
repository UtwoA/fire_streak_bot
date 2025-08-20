from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    TZ: str = 'Europe/Moscow'

    class Config:
        env_file = '.env'

settings = Settings()
