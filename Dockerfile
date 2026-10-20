FROM node:22-alpine AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend ./
RUN pnpm build

FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml backend/ ./backend/
RUN pip install --no-cache-dir ./backend
COPY --from=web /app/frontend/dist ./frontend/dist
WORKDIR /app/backend
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
