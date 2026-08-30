FROM python:3.14-slim AS builder

WORKDIR /src/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.14-slim

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /src
# Copy exactly what is needed while preserving directory structure
COPY backend/ ./backend/
COPY models/ ./models/
COPY decision_engine/ ./decision_engine/
COPY knowledge_runtime/ ./knowledge_runtime/
COPY knowledge-base/ ./knowledge-base/
COPY digital_twin/ ./digital_twin/
COPY datasets/ ./datasets/

# Start the app from the backend directory
WORKDIR /src/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
