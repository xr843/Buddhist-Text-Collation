# Default to upstream registries — China-mainland users can opt into
# faster mirrors via build args:
#   docker build \
#     --build-arg APT_MIRROR=https://mirrors.aliyun.com \
#     --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
#     -t buddhist-text-backend backend/
ARG APT_MIRROR=
ARG PIP_INDEX_URL=https://pypi.org/simple

FROM python:3.11-slim

LABEL maintainer="Buddhist Text Platform Team"
LABEL description="Backend service for Buddhist Text Platform"

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Re-declare ARGs after FROM so they're visible inside the stage.
ARG APT_MIRROR
ARG PIP_INDEX_URL

# Optional apt mirror swap (no-op when APT_MIRROR is unset).
RUN if [ -n "$APT_MIRROR" ]; then \
      sed -i "s|http://deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
    fi

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" -r requirements.txt

COPY . .

RUN mkdir -p uploads exports logs

EXPOSE 8000

# 单 worker 默认值是因为后端有 in-process 状态（local file caches）；
# 横向扩展前请先把这些状态搬到 Redis / shared volume。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
