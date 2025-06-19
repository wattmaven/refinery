# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WattMaven Refinery is a FastAPI-based REST API service that processes and refines documents (PDFs, images, etc.) into structured JSON output using OCR and LLM technologies.

## Development Commands

```bash
# Setup virtual environment
make venv

# Install dependencies
source .venv/bin/activate
uv sync --all-packages

# Run development server with hot reload
make dev

# Run tests
make test

# Linting and formatting
make lint-check    # Check code with ruff
make lint-fix      # Auto-fix linting issues
make format-check  # Check code formatting
make format-fix    # Auto-format code
make fix           # Run all fixes (lint + format)

# CI checks
make ci-smoke-test
```

## Architecture

### Core Processing Flow
1. **Document Input**: Direct upload, URL, or S3 reference
2. **OCR Processing**: Mistral AI extracts text from documents
3. **Summarization**: OpenAI creates a summary of extracted text
4. **Structured Output**: OpenAI generates JSON matching provided schema

### Key Directories
- `src/refinery/features/`: Business logic modules
  - `presigned_url/`: S3 presigned URL generation
  - `refinement/`: OCR and LLM processors
- `src/refinery/routers/`: FastAPI route handlers
- `tests/`: Unit and integration tests

### API Endpoints
- `GET /`: Health check
- `POST /refine/url`: Process document from URL
- `POST /refine/upload`: Process uploaded file
- `POST /refine/s3`: Process S3 object

### Environment Configuration
Required environment variables:
- `MISTRAL_API_KEY`: For OCR processing
- `OPENAI_API_KEY`: For LLM processing
- `REFINERY_S3_*`: Optional S3 configuration for private bucket access

### JSON Schema Requirements
All refinement endpoints require a Draft 7 JSON schema with:
- `"$schema": "https://json-schema.org/draft-07/schema#"`
- `"type": "object"`
- `"strict": true`
- Defined `properties` and `required` fields

Follow OpenAI's structured output schema guidelines for best results.

### Testing Strategy
- Unit tests: `pytest -m unit`
- Integration tests: `pytest -m integration`
- Test data available in `testdata/` directory

### Important Notes
- Python 3.13+ required
- Uses `uv` package manager (not pip)
- Pre-commit hooks via lefthook check for secrets and code quality
- All git commits follow conventional commit format