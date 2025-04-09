from openai import OpenAI

from refinery.settings import settings

client = OpenAI(
    api_key=settings.openai_api_key,
)
