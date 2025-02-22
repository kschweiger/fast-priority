FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Copy the project into the image
ADD . /app

WORKDIR /app
RUN uv sync --frozen --no-dev --no-group test

CMD ["uv", "run", "--no-dev", "--no-group", "test", "run-fast-priority"]
