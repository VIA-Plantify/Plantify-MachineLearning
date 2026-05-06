from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GRPC_HOST: str = "localhost"
    GRPC_PORT: int = 10081

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def grpc_address(self) -> str:
        return f"{self.GRPC_HOST}:{self.GRPC_PORT}"


settings = Settings()