import json

from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError


def is_json_schema_draft_7(value: dict) -> dict:
    """
    Validate the JSON schema to check it is valid and is a draft-7 schema.

    Args:
        value: The JSON schema to validate.

    Returns:
        The JSON schema if it is valid.
    """
    try:
        Draft7Validator.check_schema(value)
        return value
    except SchemaError as e:
        raise ValueError(e)


def is_json_schema_draft_7_string(value: str) -> dict:
    """
    Validate the JSON schema to check it is valid and is a draft-7 schema.
    """
    print("X")
    try:
        json_schema = json.loads(value)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON schema")

    is_json_schema_draft_7(json_schema)
    return value
