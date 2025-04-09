from dataclasses import dataclass, field
from enum import Enum
from mimetypes import guess_type

from refinery.ocr.mistral import client


class SupportedDocumentContentTypes(Enum):
    """
    Supported document content types.
    """

    PDF = "application/pdf"


class SupportedImageContentTypes(Enum):
    """
    Supported image content types.
    """

    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"


@dataclass
class OCRPageEvaluation:
    """
    The evaluation of the OCR response.
    """

    # The page number of the OCR response.
    page_number: int
    # The markdown evaluation of the OCR response.
    markdown: str


@dataclass
class OCREvaluation:
    # The evaluations of the OCR response.
    pages: list[OCRPageEvaluation]
    # The combined markdown of the OCR response.
    combined_markdown: str = field(init=False)

    def __post_init__(self):
        self.combined_markdown = combine_evaluations(self.pages)


def combine_evaluations(evaluations: list[OCRPageEvaluation]) -> str:
    """
    Combine the evaluations into a single string.

    Useful for reasoning about the OCR response.
    """
    return "\n\n\\pagebreak\n\n".join(
        [
            f"Page {evaluation.page_number}:\n{evaluation.markdown}"
            for evaluation in evaluations
        ]
    )


async def process_url(url: str) -> OCREvaluation:
    """
    Process a URL and return the OCR response.

    Args:
        url: The URL to process.

    Returns:
        A list of evaluations.
    """
    type, _ = guess_type(url)
    if type == SupportedDocumentContentTypes.PDF:
        # Process as a document
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": url,
            },
            include_image_base64=True,
        )

        return OCREvaluation(
            pages=[
                OCRPageEvaluation(page_number=page.index, markdown=page.markdown)
                for page in response.pages
            ],
        )
    elif type in SupportedImageContentTypes:
        # Process as an image
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": url,
            },
            include_image_base64=True,
        )

        return OCREvaluation(
            pages=[
                OCRPageEvaluation(page_number=page.index, markdown=page.markdown)
                for page in response.pages
            ],
        )
    else:
        raise ValueError("URL does not point to a valid document or image")
