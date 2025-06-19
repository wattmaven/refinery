from abc import abstractmethod
from dataclasses import dataclass
from typing import TypedDict

from refinery.features.structured_output.structured_output_processor import (
    ContextPrompt,
    StructuredOutputProcessor,
)


class OutputWithConfidence(TypedDict):
    """Structured output with confidence scores."""

    output: dict
    confidence: dict[str, float]


@dataclass
class StructuredOutputWithConfidenceResult:
    """Result containing structured output and confidence scores."""

    output: dict
    field_scores: dict[str, float] | None = None
    schema_matching_confidence: float | None = None


class StructuredOutputWithConfidenceProcessor(StructuredOutputProcessor):
    """
    A processor that returns structured output along with confidence scores.
    """

    @abstractmethod
    def process_with_confidence(
        self,
        json_schema: dict,
        text: str,
        context: ContextPrompt | None = None,
    ) -> StructuredOutputWithConfidenceResult:
        """
        Process the structured output and return confidence scores.

        Args:
            json_schema: The JSON schema to use for the structured output.
            text: The text to process.
            context: The context to use for the structured output.

        Returns:
            The structured output with confidence scores.
        """
        pass

    def process(
        self,
        json_schema: dict,
        text: str,
        context: ContextPrompt | None = None,
    ) -> dict:
        """
        Process the structured output (compatibility method).

        This method maintains compatibility with the base class by returning
        only the output without confidence scores.
        """
        result = self.process_with_confidence(json_schema, text, context)
        return result.output
