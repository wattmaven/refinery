import json

import pytest

from refinery.validators.json_schema import (
    is_json_schema_draft_7,
    is_json_schema_draft_7_string,
)


@pytest.mark.unit
def test_valid_is_json_schema_draft_7():
    """Test that the is_json_schema_draft_7 function handles a valid JSON schema"""
    json_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    assert is_json_schema_draft_7(json_schema) == json_schema


@pytest.mark.unit
def test_invalid_is_json_schema_draft_7():
    """Test that the is_json_schema_draft_7 function handles an invalid JSON schema"""
    json_schema = {
        "type": "object",
        # `any` is not valid.
        "properties": {"name": {"type": "any"}},
    }
    with pytest.raises(ValueError):
        is_json_schema_draft_7(json_schema)


@pytest.mark.unit
def test_valid_is_json_schema_draft_7_string():
    """Test that the is_json_schema_draft_7_string handles a valid JSON schema string"""
    json_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }

    json_schema_string = json.dumps(json_schema)
    result = is_json_schema_draft_7_string(json_schema_string)
    result_dict = json.loads(result)

    assert result_dict == json_schema


@pytest.mark.unit
def test_invalid_is_json_schema_draft_7_string():
    """Test that the is_json_schema_draft_7_string handles an invalid JSON schema string"""
    json_schema_string = "invalid"
    with pytest.raises(ValueError):
        is_json_schema_draft_7_string(json_schema_string)
