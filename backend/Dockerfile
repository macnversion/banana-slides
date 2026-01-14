# 镜像源配置参数（可通过 build args 覆盖）
ARG DOCKER_REGISTRY=
ARG APT_MIRROR=
ARG PYPI_INDEX_URL=

# 使用 Python 3.10 作为基础镜像
FROM ${DOCKER_REGISTRY:-}python:3.10-slim

# 重新声明ARG（FROM之后ARG作用域失效，需要重新声明）
ARG APT_MIRROR=
ARG PYPI_INDEX_URL=

# 设置工作目录
WORKDIR /app

# 安装系统依赖和 Pixi
RUN if [ -n "$APT_MIRROR" ]; then \
        if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
            sed -i "s@deb.debian.org@$APT_MIRROR@g" /etc/apt/sources.list.d/debian.sources; \
        else \
            echo "Warning: /etc/apt/sources.list.d/debian.sources not found, skipping mirror setup." >&2; \
        fi; \
    fi && \
    apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://pixi.sh/install.sh | bash \
    && ln -s /root/.pixi/bin/pixi /usr/local/bin/pixi

# 复制项目配置文件
COPY pixi.toml ./
COPY pixi.lock* ./

# 配置 PyPI 镜像源（如果指定）
ENV PYPI_INDEX_URL=${PYPI_INDEX_URL}

# 安装 Python 依赖
# 如果有 pixi.lock 文件则使用 --frozen，否则生成新的锁定文件
RUN if [ -f pixi.lock ]; then \
        pixi install --frozen; \
    else \
        pixi install; \
    fi

# 复制后端代码
COPY backend/ ./backend/

# 复制 pyproject.toml（pytest 配置需要）
COPY pyproject.toml ./

# 创建必要的目录
RUN mkdir -p /app/backend/instance /app/uploads

ENV PYTHONPATH=/app
ENV FLASK_APP=backend/app.py

# 暴露端口
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["sh", "-c", "curl -f http://localhost:${PORT:-5000}/health || exit 1"]

# 启动应用
CMD ["sh", "-c", "cd backend && pixi run alembic upgrade head && pixi run python app.py"]
