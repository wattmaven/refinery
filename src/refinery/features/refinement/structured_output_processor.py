from abc import ABC, abstractmethod
from dataclasses import dataclass

DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant that can process text and return a structured output.

Read the text and return the structured output.
"""

DEFAULT_CONTEXT_PROMPT = """
Here is some context that may be relevant to the text you are given:

{context}
"""


@dataclass
class ContextPrompt:
    """
    A context prompt for a structured output processor.
    """

    # The prompt template to use for the context.
    prompt_template: str = DEFAULT_CONTEXT_PROMPT
    # The context to use for the prompt.
    context: str | None = None
    # The complete prompt to use for the structured output processor.
    # If not provided, this will be None.
    prompt: str | None = None

    def __post_init__(self):
        if self.context is not None:
            self.prompt = self.prompt_template.format(context=self.context)

    def __str__(self):
        return self.prompt


class StructuredOutputProcessor(ABC):
    """
    A processor that can process structured output.
    """

    # The system prompt to use for the structured output processor.
    # Should be complete without any placeholders.
    system_prompt: str

    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt

    @abstractmethod
    def process(
        self,
        json_schema: dict,
        text: str,
        context: ContextPrompt | None = None,
    ) -> dict:
        """
        Process the structured output.

        Args:
            json_schema: The JSON schema to use for the structured output.
            text: The text to process.
            context: The context to use for the structured output.

        Returns:
            The structured output.
        """
        pass
