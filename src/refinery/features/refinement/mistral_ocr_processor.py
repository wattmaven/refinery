from enum import Enum
from mimetypes import guess_type

from mistralai import Mistral

from refinery.features.refinement.ocr_processor import (
    File,
    OCRPageResult,
    OcrProcessor,
    OcrResult,
)


class SupportedDocumentContentTypes(Enum):
    """
    Supported document content types.
    """

    PDF = "application/pdf"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ODT = "application/vnd.oasis.opendocument.text"


class SupportedImageContentTypes(Enum):
    """
    Supported image content types.
    """

    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"
    AVIF = "image/avif"


class MistralOcrProcessor(OcrProcessor):
    # The Mistral client to use for the processor.
    mistral_client: Mistral

    """
    A processor that uses Mistral to process OCR responses.
    """

    def __init__(self, mistral_client: Mistral) -> None:
        self.mistral_client = mistral_client

    def process_url(self, url: str) -> OcrResult:
        type, _ = guess_type(url)
        if type in SupportedDocumentContentTypes:
            # Process as a document
            response = self.mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": url,
                },
                include_image_base64=True,
            )

            return OcrResult(
                pages=[
                    OCRPageResult(page_number=page.index, markdown=page.markdown)
                    for page in response.pages
                ],
            )
        elif type in SupportedImageContentTypes:
            # Process as an image
            response = self.mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": url,
                },
                include_image_base64=True,
            )

            return OcrResult(
                pages=[
                    OCRPageResult(page_number=page.index, markdown=page.markdown)
                    for page in response.pages
                ],
            )
        else:
            raise ValueError("URL does not point to a valid document or image")

    def process_file(self, file: File) -> OcrResult:
        # Upload the file
        uploaded_file_response = self.mistral_client.files.upload(
            file={
                "file_name": file.filename,
                "content": file.file.read(),
            },
            purpose="ocr",
        )

        # Get a signed URL for the file
        signed_url_response = self.mistral_client.files.get_signed_url(
            file_id=uploaded_file_response.id
        )
        processed = self.process_url(signed_url_response.url)

        # Delete the file
        self.mistral_client.files.delete_async(file_id=uploaded_file_response.id)

        return processed
