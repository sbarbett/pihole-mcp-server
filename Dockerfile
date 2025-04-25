FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv pip install -e . --system

# Copy application code
COPY main.py .
COPY tools/ ./tools/
COPY resources/ ./resources/
COPY prompts/ ./prompts/

# Expose the port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 