from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017/agentmarket"
    secret_key: str = "your-secret-key"
    openai_api_key: str = "your-openai-api-key"

    class Config:
        env_file = ".env"

settings = Settings()
