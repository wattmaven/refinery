import json

from openai import BadRequestError, OpenAI

from refinery.features.structured_output.structured_output_processor import (
    DEFAULT_SYSTEM_PROMPT,
    ContextPrompt,
)
from refinery.features.structured_output.structured_output_with_confidence import (
    StructuredOutputWithConfidenceProcessor,
    StructuredOutputWithConfidenceResult,
)
from refinery.logger import logger

DEFAULT_CONFIDENCE_SYSTEM_PROMPT = """
You are a helpful assistant that can process text and return a structured output with confidence scores.

Read the text and return the structured output. For each field in your output, assess your confidence level based on:
- How clearly the information appears in the source text
- Whether you had to infer or guess any values
- The quality and clarity of the source material

Your response should include confidence scores where:
- 1.0 = Very confident, information explicitly stated
- 0.8-0.9 = Confident, minor inference required
- 0.6-0.7 = Moderately confident, some inference or uncertainty
- 0.4-0.5 = Low confidence, significant guessing
- Below 0.4 = Very low confidence, mostly guessed

Always be honest about your confidence levels.
"""


class OpenAIStructuredOutputWithConfidenceProcessor(
    StructuredOutputWithConfidenceProcessor
):
    """
    OpenAI structured output processor that includes confidence scoring.
    """

    def __init__(
        self,
        openai_client: OpenAI,
        system_prompt: str = DEFAULT_CONFIDENCE_SYSTEM_PROMPT,
    ) -> None:
        super().__init__(system_prompt=system_prompt)
        self.openai_client = openai_client

    def _create_confidence_schema(self, original_schema: dict) -> dict:
        """
        Create a wrapper schema that includes both the original output and confidence scores.
        """
        # Get the properties from the original schema
        original_properties = original_schema.get("properties", {})

        # Create field_scores schema based on original properties
        field_scores_properties = {
            field: {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": f"Confidence score for the '{field}' field",
            }
            for field in original_properties.keys()
        }

        # Create a copy of the original schema without the top-level metadata
        output_schema = {
            "type": "object",
            "properties": original_schema.get("properties", {}),
            "required": original_schema.get("required", []),
            "additionalProperties": original_schema.get("additionalProperties", False),
        }

        # Add other properties if they exist (but not $schema or strict at this level)
        for key in ["title", "description"]:
            if key in original_schema:
                output_schema[key] = original_schema[key]

        return {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "type": "object",
            "strict": True,
            "properties": {
                "output": output_schema,
                "confidence": {
                    "type": "object",
                    "properties": {
                        # The overall confidence score
                        # Indicates the overall confidence in the extraction
                        "overall": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Overall confidence in the extraction",
                        },
                        # The field scores
                        # Indicates the confidence in each field
                        # For example, if the input schema has a field "name", the field_scores will have a "name" key
                        # with a confidence score between 0 and 1
                        "field_scores": {
                            "type": "object",
                            "properties": field_scores_properties,
                            "required": list(field_scores_properties.keys()),
                            "additionalProperties": False,
                        },
                    },
                    "required": ["overall", "field_scores"],
                    "additionalProperties": False,
                },
            },
            "required": ["output", "confidence"],
            "additionalProperties": False,
        }

    def process_with_confidence(
        self,
        json_schema: dict,
        text: str,
        context: ContextPrompt | None = None,
    ) -> StructuredOutputWithConfidenceResult:
        """
        Process the structured output and return confidence scores using OpenAI.
        """
        # Create the confidence-aware schema
        confidence_schema = self._create_confidence_schema(json_schema)

        # Build the system prompt
        system_prompt = self.system_prompt
        if context is not None and context.prompt is not None:
            system_prompt = f"{system_prompt}\n\n{context.prompt}"

        logger.info(
            "Processing structured output with confidence",
            model="gpt-4o-mini",
            json_schema=json_schema,
            has_context=context is not None,
        )

        try:
            # Use the structured output API (same as OpenAIStructuredOutputProcessor)
            response = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "json_schema_with_confidence",
                        "schema": confidence_schema,
                        "strict": True,
                    },
                },
            )

            # Parse the response as a JSON object
            parsed_response = json.loads(response.output[0].content[0].text)

            logger.info(
                "Structured output with confidence processed successfully",
                model="gpt-4o-mini",
                overall_confidence=parsed_response.get("confidence", {}).get("overall"),
            )

            # Extract the results
            output = parsed_response["output"]
            confidence_data = parsed_response.get("confidence", {})

            return StructuredOutputWithConfidenceResult(
                output=output,
                field_scores=confidence_data.get("field_scores"),
                schema_matching_confidence=confidence_data.get("overall"),
            )

        except BadRequestError as e:
            logger.error(
                "Bad request error when processing structured output with confidence",
                error=str(e),
                model="gpt-4o-mini",
            )
            raise ValueError(f"Bad request error: {e}")
        except Exception as e:
            logger.error(
                "Unexpected error when processing structured output with confidence",
                error=str(e),
                model="gpt-4o-mini",
            )
            raise
