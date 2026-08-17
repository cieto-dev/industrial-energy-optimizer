import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./optimizer.db"
    )

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key"
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "True"
    ).lower() == "true"

    PORT: int = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )


settings = Settings()