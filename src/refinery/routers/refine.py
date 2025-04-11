import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from refinery.ocr.ocr import delete_file, process_file, process_url
from refinery.s3.s3 import get_object_presigned_url
from refinery.settings import settings
from refinery.structured_output.structured_output import get_structured_output
from refinery.validators.json_schema import (
    is_json_schema_draft_7,
    is_json_schema_draft_7_string,
)

router = APIRouter(
    prefix="/refine",
    tags=["refine"],
)

example_json_schema_dict = {
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
example_json_schema_str = json.dumps(example_json_schema_dict)
example_image_url_lorem_ipsum = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/lorem-ipsum.jpg"
example_image_url_slavery_in_the_united_states = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/slavery-in-the-united-states.jpg"
example_s3_bucket = "refinery-development"
example_s3_key = "lorem-ipsum.jpg"


class Refined(BaseModel):
    """
    The base model for a refined document.
    """

    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema that was used to refine the document",
        examples=[example_json_schema_dict],
    )
    output: dict = Field(..., description="The output of the refined document")
    context: str | None = Field(
        None, description="The context that was used to refine the document"
    )


class RefineUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(
        ...,
        description="The URL to refine",
        examples=[
            example_image_url_lorem_ipsum,
            example_image_url_slavery_in_the_united_states,
        ],
    )
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema to use for the structured output",
        examples=[example_json_schema_dict],
    )
    context: str | None = Field(
        None, description="The context to use for the structured output"
    )


class RefinedUrlResponse(Refined):
    url: str = Field(
        ...,
        description="The URL that was refined",
        examples=[
            example_image_url_lorem_ipsum,
            example_image_url_slavery_in_the_united_states,
        ],
    )


@router.post(
    "/url",
    summary="Refine a URL",
    description="Refine a publicly accessible remote URL.",
    response_model=RefinedUrlResponse,
)
async def refine_url(request: RefineUrlRequest):
    processed = await process_url(request.url)
    output = await get_structured_output(
        request.json_schema,
        processed.combined_markdown,
        context=request.context,
    )

    return RefinedUrlResponse(
        url=request.url,
        json_schema=request.json_schema,
        output=output,
        context=request.context,
    )


class RefinedUploadResponse(Refined):
    filename: str = Field(
        ...,
        description="The filename of the file that was refined",
    )


@router.post(
    "/upload",
    summary="Refine an uploaded file",
    description="Refine an uploaded file.",
    response_model=RefinedUploadResponse,
)
async def refine_file(
    file: Annotated[UploadFile, File(description="A file read as UploadFile")],
    json_schema: Annotated[
        str,
        AfterValidator(is_json_schema_draft_7_string),
        Form(
            description="JSON schema for structured output",
            examples=[example_json_schema_str],
        ),
    ],
    context: Annotated[
        str | None, Form(description="The context to use for the structured output")
    ] = None,
):
    loaded_json_schema = json.loads(json_schema)

    processed = await process_file(file)
    output = await get_structured_output(
        loaded_json_schema,
        processed.combined_markdown,
        context=context,
    )

    return RefinedUploadResponse(
        filename=file.filename,
        json_schema=loaded_json_schema,
        output=output,
        context=context,
    )


class RefineS3Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object to refine",
        examples=[example_s3_bucket],
    )
    key: str = Field(
        ...,
        description="The key of the S3 object to refine",
        examples=[example_s3_key],
    )
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema to use for the structured output",
        examples=[example_json_schema_dict],
    )
    context: str | None = Field(
        None, description="The context to use for the structured output"
    )


class RefinedS3Response(Refined):
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object that was refined",
        examples=[example_s3_bucket],
    )
    key: str = Field(
        ...,
        description="The key of the S3 object that was refined",
        examples=[example_s3_key],
    )


@router.post(
    "/s3",
    summary="Refine an S3 object",
    description="Refine an S3 object.",
    response_model=RefinedS3Response,
)
async def refine_s3(request: RefineS3Request):
    # Check that the S3 configuration is set.
    if (
        settings.refinery_s3_endpoint_url is None
        or settings.refinery_s3_access_key_id is None
        or settings.refinery_s3_secret_access_key is None
    ):
        raise HTTPException(status_code=500, detail="S3 is not configured")

    # Get a presigned URL for the S3 object
    presigned_url = await get_object_presigned_url(request.bucket, request.key)
    processed = await process_url(presigned_url)
    output = await get_structured_output(
        request.json_schema,
        processed.combined_markdown,
        context=request.context,
    )

    return RefinedS3Response(
        bucket=request.bucket,
        key=request.key,
        json_schema=request.json_schema,
        output=output,
        context=request.context,
    )
