# refinery

A service for refining documents.

## Development

### Setup

Install the following external dependencies:

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Running the application

```bash
# Create the virtual environment
make

# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
uv sync --all-packages

# Run the application in development mode
make dev
```

## Overview

This service is a FastAPI application that provides a REST API for refining documents into a JSON object matching a
given JSON schema.

### Refining documents

Documents can be refined by uploading them directly or by providing a URL to a file hosted on S3.

Each document is refined using a combination of OCR, LLM, and post-processing steps.

The solution currently uses:

- [Mistral](https://mistral.ai/) for OCR and document extraction.
- [OpenAI](https://openai.com/) for LLM processing and structured output.

Schemas must follow
[OpenAI's supported schemas](https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?api-mode=responses#supported-schemas).

It's recommended that if you either model the schema after this guideline, or create another that is compatible with OpenAI's structured output.
This ensures the best output.

Note that **model and platform selection is subject to change** as we continue to experiment.

#### Direct Upload

The service supports uploading documents directly from the client.

#### URL

The service allows you to specify a URL to a file to refine.

This will work with any file that is hosted on the internet, such as a PDF or image.

The document **must be publicly accessible**.

#### S3

The service allows you to specify private S3 buckets and files to refine.

This will also work with any other object storage that uses the S3 API, such as
[Cloudflare R2](https://developers.cloudflare.com/r2/).

To enable this, set the following environment variables:

```bash
REFINERY_S3_ENDPOINT_URL=
REFINERY_S3_ACCESS_KEY_ID=
REFINERY_S3_SECRET_ACCESS_KEY=
```

See [.env.example](./.env.example) for more details.

## Tests

Note that to run tests you **must provide all credentials** to accurately test integrations.

### Test Data

The [testdata](./testdata) directory contains a collection of documents that can be used to test the application.

### Sources

- [lorem-ipsum.jpg](./testdata/lorem-ipsum.jpg): A simple image of lorem ipsum text.
  [Source](https://commons.wikimedia.org/wiki/File:Test_OCR_document.jpg) CC0 1.0.
- [slavery-in-the-united-states.pdf](./testdata/slavery-in-the-united-states.pdf): A simple image of text that is of variable quality.
  [Source](https://commons.wikimedia.org/wiki/File:Test_OCR_document_2.jpg) Public Domain.
- [the-quick-brown-fox-jumps-over-the-lazy-dog.odt](./testdata/the-quick-brown-fox-jumps-over-the-lazy-dog.odt): A simple ODT containing placeholder text.
- [the-quick-brown-fox-jumps-over-the-lazy-dog.pdf](./testdata/the-quick-brown-fox-jumps-over-the-lazy-dog.pdf): A simple PDF containing placeholder text.
