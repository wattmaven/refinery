from dataclasses import dataclass
from typing import Optional


@dataclass
class ConfidenceCalculator:
    """
    Calculates overall confidence scores based on multiple factors.
    """

    # Weights for different components
    ocr_weight: float = 0.3
    summarization_weight: float = 0.2
    schema_matching_weight: float = 0.5

    def calculate_overall_confidence(
        self,
        ocr_confidence: Optional[float] = None,
        summarization_confidence: Optional[float] = None,
        schema_matching_confidence: Optional[float] = None,
    ) -> float:
        """
        Calculate overall confidence score based on available component scores.

        Args:
            ocr_confidence: Confidence in OCR extraction (0-1)
            summarization_confidence: Confidence in summarization (0-1)
            schema_matching_confidence: Confidence in schema matching (0-1)

        Returns:
            Overall confidence score (0-1)
        """
        scores = []
        weights = []

        if ocr_confidence is not None:
            scores.append(ocr_confidence)
            weights.append(self.ocr_weight)

        if summarization_confidence is not None:
            scores.append(summarization_confidence)
            weights.append(self.summarization_weight)

        if schema_matching_confidence is not None:
            scores.append(schema_matching_confidence)
            weights.append(self.schema_matching_weight)

        if not scores:
            # If no scores available, return a default
            return 0.5

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average
        overall = sum(
            score * weight for score, weight in zip(scores, normalized_weights)
        )

        return round(overall, 3)

    def estimate_ocr_confidence(self, text_length: int, page_count: int) -> float:
        """
        Estimate OCR confidence based on heuristics.

        Args:
            text_length: Total length of extracted text
            page_count: Number of pages processed

        Returns:
            Estimated OCR confidence (0-1)
        """
        # Simple heuristic: more text generally means better extraction
        # Adjust these thresholds based on your document types
        avg_chars_per_page = text_length / page_count if page_count > 0 else 0

        if avg_chars_per_page < 100:
            return 0.3  # Very little text extracted
        elif avg_chars_per_page < 500:
            return 0.6  # Moderate amount of text
        elif avg_chars_per_page < 1500:
            return 0.8  # Good amount of text
        else:
            return 0.9  # Excellent text extraction

    def estimate_summarization_confidence(
        self, original_length: int, summary_length: int
    ) -> float:
        """
        Estimate summarization confidence based on compression ratio.

        Args:
            original_length: Length of original text
            summary_length: Length of summary

        Returns:
            Estimated summarization confidence (0-1)
        """
        if original_length == 0:
            return 0.3

        compression_ratio = summary_length / original_length

        # Ideal compression ratio is between 0.1 and 0.3
        if 0.1 <= compression_ratio <= 0.3:
            return 0.9
        elif 0.05 <= compression_ratio <= 0.4:
            return 0.7
        elif compression_ratio < 0.05:
            return 0.5  # Too compressed, might lose information
        else:
            return 0.6  # Not compressed enough, might not be a good summary
