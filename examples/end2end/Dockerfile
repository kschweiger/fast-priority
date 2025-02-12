FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv venv
RUN uv pip install fastapi[standard]

CMD ["uv", "run", "fastapi", "run", "app.py", "--host", "0.0.0.0"]

