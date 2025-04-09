import json

from openai import BadRequestError

from refinery.structured_output.openai import client

DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant that can parse text into a JSON object.

Extract the JSON object from the text you are given.
"""

DEFAULT_CONTEXT_PROMPT = """
Here is some context that may be relevant to the text you are given:

{context}
"""


async def get_structured_output(
    json_schema: dict,
    text: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    context_prompt: str = DEFAULT_CONTEXT_PROMPT,
    context: str | None = None,
) -> dict:
    """
    Get a structured output from OpenAI.

    Args:
        json_schema: The JSON schema to use for the structured output.
        text: The text to parse into a JSON object.
        system_prompt: The system prompt to use for the structured output.
        context: The context to use for the structured output.
    Returns:
        The structured output.
    """
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                # Add the context prompt if it is provided
                # {"role": "system", "content": context_prompt.format(context=context)}
                # if context
                # else None,
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
