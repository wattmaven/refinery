import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from refinery.examples import (
    example_image_url_lorem_ipsum,
    example_image_url_slavery_in_the_united_states,
    example_json_schema_dict,
)
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
    error: str | None = Field(None, description="Error if processing failed")


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
    context: str = Field(
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
    try:
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
    except Exception as e:
        return RefinedUrlResponse(
            url=request.url,
            json_schema=request.json_schema,
            output={},
            context=request.context,
            error=str(e),
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
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="A file read as UploadFile")],
    json_schema: Annotated[
        str,
        AfterValidator(is_json_schema_draft_7_string),
        Form(description="JSON schema for structured output"),
    ],
    context: Annotated[str, Form(description="Optional context")] = None,
):
    try:
        loaded_json_schema = json.loads(json_schema)

        processed, mistral_file_id = await process_file(file)
        # Delete the file from Mistral after the request is processed
        background_tasks.add_task(delete_file, mistral_file_id)

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
    except Exception as e:
        return RefinedUploadResponse(
            filename=file.filename,
            json_schema=loaded_json_schema,
            output={},
            context=context,
            error=str(e),
        )


class RefineS3Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object to refine",
    )
    key: str = Field(
        ...,
        description="The key of the S3 object to refine",
    )
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema to use for the structured output",
        examples=[example_json_schema_dict],
    )
    context: str = Field(
        None, description="The context to use for the structured output"
    )


class RefinedS3Response(Refined):
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object that was refined",
    )
    key: str = Field(
        ...,
        description="The key of the S3 object that was refined",
    )


@router.post(
    "/s3",
    summary="Refine an S3 object",
    description="Refine an S3 object.",
    response_model=RefinedS3Response,
)
async def refine_s3(request: RefineS3Request):
    # Check that the S3 configuration is set
    if (
        settings.refinery_s3_endpoint_url is None
        or settings.refinery_s3_access_key_id is None
        or settings.refinery_s3_secret_access_key is None
    ):
        raise HTTPException(status_code=500, detail="S3 is not configured")

    try:
        # Get a presigned URL for the S3 object
        presigned_url = await get_object_presigned_url(request.bucket, request.key)
        print(presigned_url)
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
    except Exception as e:
        return RefinedS3Response(
            bucket=request.bucket,
            key=request.key,
            json_schema=request.json_schema,
            output={},
            context=request.context,
            error=str(e),
        )
