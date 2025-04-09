import json
from typing import Annotated

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from mistralai import Mistral
from openai import OpenAI
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from refinery.features.presigned_url.s3_presigned_url_generator import (
    S3PresignedUrlGenerator,
)
from refinery.features.refinement.mistral_ocr_processor import MistralOcrProcessor
from refinery.features.refinement.ocr_processor import OcrProcessor
from refinery.features.refinement.openai_structured_output_processor import (
    OpenAIStructuredOutputProcessor,
)
from refinery.features.refinement.openai_summarization_processor import (
    OpenAISummarizationProcessor,
)
from refinery.features.refinement.structured_output_processor import (
    StructuredOutputProcessor,
)
from refinery.features.refinement.summarization_processor import SummarizationProcessor
from refinery.logger import logger
from refinery.settings import settings
from refinery.validators.json_schema import (
    is_json_schema_draft_7,
    is_json_schema_draft_7_string,
)

# Private example objects for API documentation
# Example JSON schema
_example_json_schema_dict = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/document#",
    "title": "Document",
    "description": "A document from Acme's catalog",
    "type": "object",
    "strict": True,
    "properties": {"summary": {"description": "A basic summary", "type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}
_example_json_schema_str = json.dumps(_example_json_schema_dict)
_example_json_schema_url = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/example-json-schema.json"
# Example URLs
_example_image_url_lorem_ipsum = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/lorem-ipsum.jpg"
_example_image_url_slavery_in_the_united_states = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/slavery-in-the-united-states.jpg"
# Example S3 objects
_example_s3_bucket = "refinery-development"
_example_s3_key = "lorem-ipsum.jpg"

router = APIRouter(
    prefix="/refine",
    tags=["refine"],
)


class CommonRefinementDependencies:
    """
    Common dependencies for refinement.

    Only put things in here that most requests will need.
    """

    # The OCR processor to use for the refinement.
    ocr_processor: OcrProcessor
    # The summarization processor to use for the refinement.
    summarization_processor: SummarizationProcessor
    # The structured output processor to use for the refinement.
    structured_output_processor: StructuredOutputProcessor

    def __init__(self):
        self.ocr_processor = MistralOcrProcessor(
            mistral_client=Mistral(
                api_key=settings.mistral_api_key,
            )
        )
        self.summarization_processor = OpenAISummarizationProcessor(
            openai_client=OpenAI(
                api_key=settings.openai_api_key,
            )
        )
        self.structured_output_processor = OpenAIStructuredOutputProcessor(
            openai_client=OpenAI(
                api_key=settings.openai_api_key,
            )
        )


class Refined(BaseModel):
    """
    The base model for a refined document.
    """

    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema that was used to refine the document",
        examples=[_example_json_schema_dict],
    )
    summary: str = Field(
        ...,
        description="The summary of the refined document",
        examples=["Lorem ipsum dolor sit amet, consectetur adipiscing elit."],
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
            _example_image_url_lorem_ipsum,
            _example_image_url_slavery_in_the_united_states,
        ],
    )
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema to use for the structured output",
        examples=[_example_json_schema_dict],
    )
    context: str | None = Field(
        None, description="The context to use for the structured output"
    )


class RefinedUrlResponse(Refined):
    url: str = Field(
        ...,
        description="The URL that was refined",
        examples=[
            _example_image_url_lorem_ipsum,
            _example_image_url_slavery_in_the_united_states,
        ],
    )


@router.post(
    "/url",
    summary="Refine a URL",
    description="Refine a publicly accessible remote URL.",
    response_model=RefinedUrlResponse,
)
async def refine_url(
    request: RefineUrlRequest,
    refinement_dependencies: Annotated[
        CommonRefinementDependencies, Depends(CommonRefinementDependencies)
    ],
):
    logger.info("Refining URL", url=request.url)

    processed = refinement_dependencies.ocr_processor.process_url(request.url)
    logger.info("Processed evaluation", combined_markdown=processed.combined_markdown)

    summary = refinement_dependencies.summarization_processor.summarize(
        processed.combined_markdown
    )
    logger.info("Summary", summary=summary)

    output = refinement_dependencies.structured_output_processor.process(
        request.json_schema,
        summary,
        context=request.context,
    )
    logger.info(
        "Output",
        json_schema=request.json_schema,
        output=output,
        context=request.context,
    )

    return RefinedUrlResponse(
        url=request.url,
        summary=summary,
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
            examples=[_example_json_schema_str],
        ),
    ],
    refinement_dependencies: Annotated[
        CommonRefinementDependencies, Depends(CommonRefinementDependencies)
    ],
    context: Annotated[
        str | None, Form(description="The context to use for the structured output")
    ] = None,
):
    loaded_json_schema = json.loads(json_schema)
    logger.info("Refining file", filename=file.filename)

    processed = refinement_dependencies.ocr_processor.process_file(file)
    logger.info("Processed evaluation", combined_markdown=processed.combined_markdown)

    summary = refinement_dependencies.summarization_processor.summarize(
        processed.combined_markdown
    )
    logger.info("Summary", summary=summary)

    output = refinement_dependencies.structured_output_processor.process(
        loaded_json_schema,
        summary,
        context=context,
    )
    logger.info(
        "Output",
        json_schema=loaded_json_schema,
        summary=summary,
        output=output,
        context=context,
    )

    return RefinedUploadResponse(
        filename=file.filename,
        summary=summary,
        json_schema=loaded_json_schema,
        output=output,
        context=context,
    )


class RefineS3Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object to refine",
        examples=[_example_s3_bucket],
    )
    key: str = Field(
        ...,
        description="The key of the S3 object to refine",
        examples=[_example_s3_key],
    )
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ...,
        description="The Draft 7 JSON schema to use for the structured output",
        examples=[_example_json_schema_dict],
    )
    context: str | None = Field(
        None, description="The context to use for the structured output"
    )


class RefinedS3Response(Refined):
    bucket: str = Field(
        ...,
        description="The bucket of the S3 object that was refined",
        examples=[_example_s3_bucket],
    )
    key: str = Field(
        ...,
        description="The key of the S3 object that was refined",
        examples=[_example_s3_key],
    )


def create_s3_presign_generator() -> S3PresignedUrlGenerator:
    return S3PresignedUrlGenerator(
        boto3_client=boto3.client(
            "s3",
            endpoint_url=settings.refinery_s3_endpoint_url,
            aws_access_key_id=settings.refinery_s3_access_key_id,
            aws_secret_access_key=settings.refinery_s3_secret_access_key,
            config=Config(
                signature_version="s3v4",
            ),
        )
    )


@router.post(
    "/s3",
    summary="Refine an S3 object",
    description="Refine an S3 object.",
    response_model=RefinedS3Response,
)
async def refine_s3(
    request: RefineS3Request,
    refinement_dependencies: Annotated[
        CommonRefinementDependencies, Depends(CommonRefinementDependencies)
    ],
    s3_presigned_url_generator: Annotated[
        S3PresignedUrlGenerator, Depends(create_s3_presign_generator)
    ],
):
    # Check that the S3 configuration is set.
    if (
        settings.refinery_s3_endpoint_url is None
        or settings.refinery_s3_access_key_id is None
        or settings.refinery_s3_secret_access_key is None
    ):
        raise HTTPException(status_code=500, detail="S3 is not configured")

    logger.info("Refining S3 object", bucket=request.bucket, key=request.key)

    # Get a presigned URL for the S3 object
    presigned_url = s3_presigned_url_generator.generate_presigned_url(
        request.bucket, request.key
    )
    logger.info("Presigned URL", presigned_url=presigned_url)

    processed = refinement_dependencies.ocr_processor.process_url(presigned_url)
    logger.info("Processed evaluation", combined_markdown=processed.combined_markdown)

    summary = refinement_dependencies.summarization_processor.summarize(
        processed.combined_markdown
    )
    logger.info("Summary", summary=summary)

    output = refinement_dependencies.structured_output_processor.process(
        request.json_schema,
        summary,
        context=request.context,
    )
    logger.info(
        "Output",
        json_schema=request.json_schema,
        summary=summary,
        output=output,
        context=request.context,
    )

    return RefinedS3Response(
        bucket=request.bucket,
        key=request.key,
        summary=summary,
        json_schema=request.json_schema,
        output=output,
        context=request.context,
    )
