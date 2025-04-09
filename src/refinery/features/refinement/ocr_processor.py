from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class OCRPageResult:
    """
    The result of the OCR response.
    """

    # The page number of the OCR response.
    page_number: int
    # The markdown result of the OCR response.
    markdown: str


def combine_results(results: list[OCRPageResult]) -> str:
    """
    Combine the results into a single string.

    Useful for reasoning about the OCR response.
    """
    return "\n\n\\pagebreak\n\n".join(
        [f"Page {result.page_number}:\n{result.markdown}" for result in results]
    )


@dataclass
class OcrResult:
    # The results of the OCR response.
    pages: list[OCRPageResult]
    # The combined markdown of the OCR response.
    combined_markdown: str = field(init=False)

    def __post_init__(self):
        self.combined_markdown = combine_results(self.pages)


@dataclass
class File:
    """
    A file to be processed.

    Mimics the FastAPI UploadFile class.
    """

    # The data of the file.
    data: bytes
    # The filename of the file.
    filename: str
    # The content type of the file.
    content_type: str


class OcrProcessor(ABC):
    """
    Processes OCR responses.
    """

    @abstractmethod
    def process_url(self, url: str) -> OcrResult:
        """
        Process the OCR response for a given URL.

        Args:
            url: The URL to process.

        Returns:
            The OCR result.
        """
        pass

    @abstractmethod
    def process_file(self, file: File) -> OcrResult:
        """
        Process the OCR response for a given file.

        Args:
            file: The file to process.

        Returns:
            The OCR result.
        """
        pass
