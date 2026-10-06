FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements-firestore.txt ./
# Set to requirements-firestore.txt to include the Firestore client.
ARG REQUIREMENTS=requirements.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS}
COPY backend/ ./
COPY --from=frontend-build /frontend/dist/ /app/frontend/dist/

# Local file storage by default; mount a volume at /app/data to keep state.
# Set STORAGE_BACKEND=firestore (and build with REQUIREMENTS=requirements-firestore.txt) to use Firestore.
ENV STORAGE_BACKEND=local
EXPOSE 8080

# One worker: timers and WebSocket connections live in process memory.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--loop", "uvloop", "--http", "h11", "--timeout-keep-alive", "300", "--ws-ping-interval", "300", "--ws-ping-timeout", "300"]
