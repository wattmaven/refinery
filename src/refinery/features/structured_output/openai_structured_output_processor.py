import json

from openai import BadRequestError, OpenAI

from refinery.features.structured_output.structured_output_processor import (
    ContextPrompt,
    StructuredOutputProcessor,
)


class OpenAIStructuredOutputProcessor(StructuredOutputProcessor):
    """
    A processor that uses OpenAI to process structured output.
    """

    # The OpenAI client to use for the processor.
    openai_client: OpenAI

    def __init__(self, openai_client: OpenAI) -> None:
        super().__init__()

        self.openai_client = openai_client

    def process(
        self, json_schema: dict, text: str, context: ContextPrompt | None = None
    ) -> dict:
        # If context is provided, add it to the system prompt.
        if context is not None:
            self.system_prompt += "\n\n" + str(context)

        try:
            response = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "json_schema",
                        "schema": json_schema,
                        "strict": True,
                    },
                },
            )

            # Parse the response as a JSON object
            return json.loads(response.output[0].content[0].text)
        except BadRequestError as e:
            raise ValueError(e.message)
        except Exception as e:
            raise e
