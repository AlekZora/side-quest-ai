# Build context is the repo root (docker build . / docker compose up --build
# from here) so this image can COPY only prototype/ — not docs/ or godot/,
# neither of which the running service needs.
FROM python:3.13-slim

WORKDIR /app

COPY prototype/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prototype/ .

EXPOSE 8000

# DATABASE_URL and OPENAI_API_KEY are not baked in here — they're read from
# the process environment at runtime (docker run -e / docker compose env_file).
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
