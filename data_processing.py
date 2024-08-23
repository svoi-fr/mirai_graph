import trafilatura
import json
from validation import validate_and_prune_json, prune_empty_and_invalid_references
from llm import chat_session

INPUT_MAX_CHARACTERS = 10000
OUTPUT_MAX_CHARACTERS = 5000
MAX_TRIES = 5

def process_url(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None, None

    doc = trafilatura.extract(downloaded, include_links=True, include_contacts=True,
                              include_formatting=True, with_metadata=True,
                              output_format='json')

    if not doc:
        return None, None

    obj = json.loads(doc)

    if "text" not in obj:
        return None, None

    original_text = obj["text"][:INPUT_MAX_CHARACTERS]
    response_text = send_to_llm_with_validation(original_text)

    return original_text, response_text

def send_to_llm_with_validation(original_text):
    initial_organizations = None
    initial_contacts = None

    for attempt in range(MAX_TRIES):
        response = chat_session.send_message(original_text)
        response_json = json.loads(response.text)

        if attempt == 0:
            initial_organizations = response_json.get("Organization", [])
            initial_contacts = response_json.get("Contact", [])

        cleaned_json = prune_empty_and_invalid_references(response_json)

        validation_errors = validate_and_prune_json(cleaned_json)  # Collect all errors
        if validation_errors:
            compacted_json = json.dumps(cleaned_json, separators=(',', ':'))
            if len(compacted_json) > OUTPUT_MAX_CHARACTERS:
              validation_errors.append(f"Output too long (length {len(compacted_json)}), trim down to {OUTPUT_MAX_CHARACTERS}.")
            print(f"Attempt {attempt + 1}: Validation failed. Reasons:")
            for error in validation_errors:
                print(f"  - {error}")
            print("Unvalidated JSON:")
            print(json.dumps(cleaned_json, indent=4))  # Print formatted JSON
            original_text = "\n".join(validation_errors) + "\n" + json.dumps(cleaned_json)
            continue

        compacted_json = json.dumps(cleaned_json, separators=(',', ':'))
        if len(compacted_json) > OUTPUT_MAX_CHARACTERS:
            print(f"Attempt {attempt + 1}: Output too long (length {len(compacted_json)}). Retrying...")

            if attempt == 0:
                trim_instruction = (
                    f"Output too long, current length {len(compacted_json)}, "
                    f"trim down to {OUTPUT_MAX_CHARACTERS} characters. "
                    "First, try to prune redundant Tasks, especially those that could be described as getting a provision. "
                    "Tasks should be actions that persons need to undertake themselves, "
                    "not necessarily linked with Provisions."
                )
            elif attempt == 1:
                trim_instruction = (
                    f"Output still too long, current length {len(compacted_json)}, "
                    f"trim down to {OUTPUT_MAX_CHARACTERS} characters. "
                    "Now, try to prune Provisions that are too specific or granular."
                )
            elif attempt >= 2:
                trim_instruction = (
                    f"Output still too long, current length {len(compacted_json)}, "
                    f"trim down to {OUTPUT_MAX_CHARACTERS} characters. "
                    "As a last resort, prune Contexts that are too general. "
                    "Contexts should be highly specific to situations described in the document."
                )

            original_text = trim_instruction + "\n" + compacted_json
            continue

        cleaned_json["Organization"] = initial_organizations
        cleaned_json["Contact"] = initial_contacts
        return json.dumps(cleaned_json, separators=(',', ':')) 

    print(f"Failed to produce valid output after {MAX_TRIES} attempts.")
    return None