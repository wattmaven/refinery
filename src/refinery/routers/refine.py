import json
from typing import Annotated, List

from fastapi import APIRouter, Body, Query
from fastapi.responses import StreamingResponse
from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from sse_starlette.sse import EventSourceResponse

from refinery.logger import logger
from refinery.ocr.ocr import process_url
from refinery.structured_output.structured_output import get_structured_output
from refinery.validators.json_schema import is_json_schema_draft_7

router = APIRouter(
    prefix="/refine",
    tags=["refine"],
)


class RefineUrlsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    urls: List[str] = Field(..., description="The URLs to refine")
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ..., description="The JSON schema to use for the structured output"
    )
    context: str = Field(
        None, description="The context to use for the structured output"
    )


class RefinedUrl(BaseModel):
    url: str = Field(..., description="The ID of the refined document")
    json_schema: Annotated[dict, AfterValidator(is_json_schema_draft_7)] = Field(
        ..., description="The JSON schema that was used to refine the document"
    )
    output: dict = Field(..., description="The output of the refined document")
    context: str | None = Field(
        None, description="The context that was used to refine the document"
    )


class RefineUrlResponse(BaseModel):
    results: list[RefinedUrl] = Field(..., description="The results of the refinement")


@router.post(
    "/urls",
    summary="Refine URLs",
    description="Refine publically accessible remote URLs.",
    response_model=RefineUrlResponse,
)
async def refine_urls(request: RefineUrlsRequest):
    async def event_generator():
        for url in request.urls:
            try:
                processed = await process_url(url)
                output = await get_structured_output(
                    request.json_schema,
                    processed.combined_markdown,
                    context=request.context,
                )

                refined = RefinedUrl(
                    url=url,
                    json_schema=request.json_schema,
                    output=output,
                    context=request.context,
                )
            except Exception as e:
                refined = RefinedUrl(
                    url=url,
                    json_schema=request.json_schema,
                    output={},
                    context=request.context,
                    error=str(e),
                )

            yield {"event": "result", "data": refined.model_dump_json()}

    return EventSourceResponse(event_generator())
