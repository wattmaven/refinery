# Examples for endpoints.
# Add any new examples to this file.

import json

# Example URLs.
example_image_url_lorem_ipsum = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/lorem-ipsum.jpg"
example_image_url_slavery_in_the_united_states = "https://raw.githubusercontent.com/wattmaven/refinery/refs/heads/feat/basic-setup/testdata/slavery-in-the-united-states.jpg"

# Example JSON schema.
example_json_schema_dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/document.schema.json",
    "strict": True,
    "title": "Document",
    "description": "A document from Acme's catalog",
    "type": "object",
    "properties": {"summary": {"description": "A basic summary", "type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}
example_json_schema_str = json.dumps(example_json_schema_dict)
