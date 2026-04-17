
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim

LABEL maintainer="Brandon Eroza <tbdonran.23@gmail.com>"
LABEL description="DevAgent API — AI-powered developer support agent"


RUN groupadd --system devagent && \
    useradd --system --gid devagent --create-home devagent

WORKDIR /app

COPY --from=builder /install /usr/local

COPY ./app ./app
USER devagent

EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]