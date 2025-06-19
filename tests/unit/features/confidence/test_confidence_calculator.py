import pytest

from refinery.features.confidence.confidence_calculator import ConfidenceCalculator


@pytest.mark.unit
def test_confidence_calculator_overall_score():
    """Test the overall confidence score calculation."""
    calculator = ConfidenceCalculator()

    # Test with all scores present
    overall = calculator.calculate_overall_confidence(
        ocr_confidence=0.8, summarization_confidence=0.7, schema_matching_confidence=0.9
    )

    # Expected: (0.8 * 0.3 + 0.7 * 0.2 + 0.9 * 0.5) = 0.24 + 0.14 + 0.45 = 0.83
    assert overall == 0.83

    # Test with partial scores
    overall = calculator.calculate_overall_confidence(
        ocr_confidence=0.8, schema_matching_confidence=0.9
    )

    # Weights: 0.3 and 0.5, normalized to 0.375 and 0.625
    # Expected: (0.8 * 0.375 + 0.9 * 0.625) = 0.3 + 0.5625 = 0.8625
    assert overall == 0.863

    # Test with no scores
    overall = calculator.calculate_overall_confidence()
    assert overall == 0.5  # Default value


@pytest.mark.unit
def test_ocr_confidence_estimation():
    """Test OCR confidence estimation based on text length."""
    calculator = ConfidenceCalculator()

    # Test with very little text
    assert calculator.estimate_ocr_confidence(50, 1) == 0.3

    # Test with moderate text
    assert calculator.estimate_ocr_confidence(300, 1) == 0.6

    # Test with good amount of text
    assert calculator.estimate_ocr_confidence(1000, 1) == 0.8

    # Test with excellent text extraction
    assert calculator.estimate_ocr_confidence(2000, 1) == 0.9

    # Test with multiple pages
    assert calculator.estimate_ocr_confidence(3000, 2) == 0.9  # 1500 chars per page


@pytest.mark.unit
def test_summarization_confidence_estimation():
    """Test summarization confidence estimation based on compression ratio."""
    calculator = ConfidenceCalculator()

    # Test ideal compression ratio (20%)
    assert calculator.estimate_summarization_confidence(1000, 200) == 0.9

    # Test good compression ratio (30%)
    assert calculator.estimate_summarization_confidence(1000, 300) == 0.9

    # Test acceptable compression ratio (35%)
    assert calculator.estimate_summarization_confidence(1000, 350) == 0.7

    # Test too compressed (3%)
    assert calculator.estimate_summarization_confidence(1000, 30) == 0.5

    # Test not compressed enough (50%)
    assert calculator.estimate_summarization_confidence(1000, 500) == 0.6

    # Test edge case: no original text
    assert calculator.estimate_summarization_confidence(0, 100) == 0.3
