FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./

# Materialize the locked runtime environment during the image build.
RUN uv sync --locked --no-install-project

# Copy application code
COPY main.py .
COPY tools/ ./tools/
COPY resources/ ./resources/
COPY prompts/ ./prompts/

# Expose the port
EXPOSE 8000

# Run the server from the environment created at build time.
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
