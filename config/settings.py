from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    grpc_host: str = "localhost"
    grpc_port: int = 10081

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def grpc_address(self) -> str:
        return f"{self.grpc_host}:{self.grpc_port}"


settings = Settings()