import json
import os
from io import BytesIO

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from refinery.routers import refine
from refinery.routers.refine import (
    RefinedS3Response,
    RefinedUploadResponse,
    RefinedUrlResponse,
    RefineS3Request,
    RefineUrlRequest,
)

app = FastAPI()
app.include_router(refine.router)

# A basic test JSON schema.
test_json_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/document.schema.json",
    "strict": True,
    "title": "Document",
    "description": "A document from Acme's catalog",
    "type": "object",
    "properties": {"summary": {"description": "A basic summary", "type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_url_image():
    """Test refining an image URL"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        body = RefineUrlRequest(
            url="https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/lorem-ipsum.jpg",
            json_schema=test_json_schema,
        )

        response = await ac.post("/refine/url", json=body.model_dump())
        response_url_response_data = response.json()
        refined_url_response = RefinedUrlResponse(**response_url_response_data)

        assert response.status_code == 200
        assert refined_url_response.url == body.url
        assert refined_url_response.output is not None
        assert "summary" in refined_url_response.output


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_url_with_context():
    """Test refining an image URL with context"""

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        body = RefineUrlRequest(
            url="https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/lorem-ipsum.jpg",
            json_schema=test_json_schema,
            context="Limit your response to only one word to describe the emotion.",
        )
        response = await ac.post("/refine/url", json=body.model_dump())
        response_url_response_data = response.json()
        refined_url_response = RefinedUrlResponse(**response_url_response_data)

        assert response.status_code == 200
        assert refined_url_response.url == body.url
        assert refined_url_response.output is not None
        assert "summary" in refined_url_response.output
        # Make sure the context has been applied
        assert refined_url_response.context == body.context
        assert len(refined_url_response.output) == 1


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_upload_image():
    """Test refining an uploaded image"""
    test_filename = "lorem-ipsum.jpg"
    test_file_path = f"testdata/{test_filename}"

    if not os.path.exists(test_file_path):
        pytest.skip(f"Test file not found at {test_file_path}")

    with open(test_file_path, "rb") as test_file:
        file_content = test_file.read()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/refine/upload",
            files={"file": (test_filename, BytesIO(file_content), "image/jpeg")},
            data={
                # Requires the JSON schema in string form.
                "json_schema": json.dumps(test_json_schema),
            },
        )
        response_upload_response_data = response.json()
        refined_upload_response = RefinedUploadResponse(**response_upload_response_data)

        assert response.status_code == 200
        assert refined_upload_response.filename == test_filename
        assert refined_upload_response.output is not None
        assert "summary" in refined_upload_response.output


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_upload_image_with_context():
    """Test refining an uploaded image with context"""
    test_filename = "lorem-ipsum.jpg"
    test_file_path = f"testdata/{test_filename}"

    if not os.path.exists(test_file_path):
        pytest.skip(f"Test file not found at {test_file_path}")

    with open(test_file_path, "rb") as test_file:
        file_content = test_file.read()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        context = "Limit your response to only one word to describe the emotion."
        response = await ac.post(
            "/refine/upload",
            files={"file": (test_filename, BytesIO(file_content), "image/jpeg")},
            data={
                "json_schema": json.dumps(test_json_schema),
                "context": context,
            },
        )
        response_upload_response_data = response.json()
        refined_upload_response = RefinedUploadResponse(**response_upload_response_data)

        assert response.status_code == 200
        assert refined_upload_response.filename == test_filename
        assert refined_upload_response.output is not None
        assert "summary" in refined_upload_response.output
        # Make sure the context has been applied
        assert refined_upload_response.context == context
        assert len(refined_upload_response.output) == 1


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_s3_image():
    """Test refining an S3 image"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        body = RefineS3Request(
            bucket="refinery-development",
            key="lorem-ipsum.jpg",
            json_schema=test_json_schema,
        )
        response = await ac.post(
            "/refine/s3",
            json=body.model_dump(),
        )
        response_s3_response_data = response.json()
        refined_s3_response = RefinedS3Response(**response_s3_response_data)

        assert response.status_code == 200
        assert refined_s3_response.bucket == body.bucket
        assert refined_s3_response.key == body.key
        assert refined_s3_response.output is not None
        assert "summary" in refined_s3_response.output


@pytest.mark.integration
@pytest.mark.anyio
async def test_refine_s3_image_with_context():
    """Test refining an S3 image with context"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        body = RefineS3Request(
            bucket="refinery-development",
            key="lorem-ipsum.jpg",
            json_schema=test_json_schema,
            context="Limit your response to only one word to describe the emotion.",
        )
        response = await ac.post(
            "/refine/s3",
            json=body.model_dump(),
        )
        response_s3_response_data = response.json()
        refined_s3_response = RefinedS3Response(**response_s3_response_data)

        assert response.status_code == 200
        assert refined_s3_response.bucket == body.bucket
        assert refined_s3_response.key == body.key
        assert refined_s3_response.output is not None
        assert "summary" in refined_s3_response.output
        # Make sure the context has been applied
        assert refined_s3_response.context == body.context
        assert len(refined_s3_response.output) == 1
