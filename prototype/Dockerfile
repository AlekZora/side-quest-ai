FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# DATABASE_URL and OPENAI_API_KEY are not baked in here — they're read from
# the process environment at runtime (docker run -e / docker compose env_file).
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
