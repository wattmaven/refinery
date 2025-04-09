FROM python:3.13-slim-bullseye@sha256:c527a33e5265d0f830994d1b3237d38840a7b7986a8b9374a4b941ac34048190

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

# Copy the application into the container
COPY . /app

# Install the application dependencies
WORKDIR /app

# Create a virtual environment first and then install the package
RUN uv venv
RUN . .venv/bin/activate && uv pip install --no-cache .

# Run the application
CMD ["/app/.venv/bin/uvicorn", "fastapi_template.main:app", "--host", "0.0.0.0", "--port", "8000"]
