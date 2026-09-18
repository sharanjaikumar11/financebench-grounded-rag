FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY config ./config
COPY scripts ./scripts
COPY evaluation ./evaluation
COPY data/processed ./data/processed

EXPOSE 8000
CMD ["uvicorn", "rag_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
