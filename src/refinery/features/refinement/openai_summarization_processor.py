from openai import BadRequestError, OpenAI

from refinery.features.refinement.summarization_processor import SummarizationProcessor


class OpenAISummarizationProcessor(SummarizationProcessor):
    """
    A processor that summarizes text using OpenAI.
    """

    openai_client: OpenAI

    def __init__(self, openai_client: OpenAI) -> None:
        super().__init__()

        self.openai_client = openai_client

    def summarize(self, text: str) -> str:
        """
        Summarize the text.
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "text"},
            )

            return response.choices[0].message.content
        except BadRequestError as e:
            raise ValueError(e.message)
        except Exception as e:
            raise e
