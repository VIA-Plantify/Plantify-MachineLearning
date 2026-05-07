FROM python:3.12-slim

WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

ENV APP_HOST=0.0.0.0
ENV APP_PORT=12080
ENV GRPC_PORT=10081
ENV GRPC_HOST=grpcserver
ENV ENVIRONMENT=production

ENV PYTHONPATH=/code:/code/.generated

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

#clone from main

RUN git clone --depth 1 --branch main https://github.com/VIA-Plantify/Plantify-MachineLearning /code

# install dependencies
RUN uv sync --frozen --no-dev

# compile grpc
RUN chmod +x /code/.scripts/compile-grpc.sh \
    && /code/.scripts/compile-grpc.sh

EXPOSE 12080

CMD ["sh", "-c", "uv run uvicorn main:app --host ${APP_HOST} --port ${APP_PORT}"]