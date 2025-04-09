from mistralai import Mistral

from refinery.settings import settings

client = Mistral(
    api_key=settings.mistral_api_key,
)
