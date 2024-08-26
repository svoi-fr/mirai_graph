import json
from scripts.add_null_fields import add_null_fields
from scripts.normalize_city_name import normalize_city_name
import json
from scripts.add_null_fields import add_null_fields
from scripts.normalize_city_name import normalize_city_name
from scripts.propagate_city_to_contacts import propagate_city_to_contacts
from scripts.match_contact_ids_to_cities import match_contact_ids_to_cities
from scripts.append_city_to_contact_id import append_city_to_contact_id
from scripts.merge_contacts_within_organization import merge_contacts_within_organization
from scripts.add_contact_cities_to_organization import add_contact_cities_to_organization
from scripts.rename_keys import rename_keys
from scripts.compare_and_cleanup_urls import compare_and_cleanup_urls
from scripts.remove_organizations_and_cleanup import remove_organizations_and_cleanup

# Define the complete default structure based on your provided schema
default_structure = {
    'Summary': {
        'id': None,
        'info': None,
        'country': None,
        'cities': [],
        'type': None
    },
    'Organization': [
        {
            'id': None,
            'info': None,
            'contacts': [],
            'website': None,
            'cities': []
        }
    ],
    'Provision': [
        {
            'id': None,
            'info': None,
            'contexts': [],
            'organizations': []
        }
    ],
    'Contact': [
        {
            'id': None,
            'address': None,
            'city': None,
            'phone': None,
            'email': None,
            'contact_page': None
        }
    ],
    'Context': [
        {
            'id': None,
            'info': None
        }
    ],
    'Task': [
        {
            'id': None,
            'info': None,
            'contexts': [],
            'provisions': []
        }
    ]
}

# Input and output file paths
input_file = '../output.jsonl'
training_output_file = 'training_set.jsonl'
validation_output_file = 'validation_set.jsonl'

# Process the JSONL file
with open(input_file, 'r') as infile, \
     open(training_output_file, 'w') as train_outfile, \
     open(validation_output_file, 'w') as val_outfile:

    json_lines = infile.readlines()
    total_lines = len(json_lines)
    validation_lines = 50
    training_lines = total_lines - validation_lines

    for idx, line in enumerate(json_lines):
        json_obj = json.loads(line)
        
        # Track whether any content was removed
        messages_to_keep = []
        
        for message in json_obj['messages']:
            if message['role'] == 'assistant':
                content = json.loads(message['content'])
                content = remove_organizations_and_cleanup(content)
                
                if content:
                    rename_keys(content)
                    compare_and_cleanup_urls(content)
                    add_null_fields(content, default_structure)
                    propagate_city_to_contacts(content)
                    match_contact_ids_to_cities(content)
                    append_city_to_contact_id(content)
                    add_contact_cities_to_organization(content)
                    merge_contacts_within_organization(content)
                    message['content'] = '```json\n' + json.dumps(content, ensure_ascii=False) + '\n```'
                    messages_to_keep.append(message)
        
        # Only keep the JSON object if there's at least one message left
        if messages_to_keep:
            json_obj['messages'] = messages_to_keep
            if idx < training_lines:
                json.dump(json_obj, train_outfile, ensure_ascii=False)
                train_outfile.write('\n')
            else:
                json.dump(json_obj, val_outfile, ensure_ascii=False)
                val_outfile.write('\n')

print(f"Processing complete. Training set saved as {training_output_file}, validation set saved as {validation_output_file}.")
