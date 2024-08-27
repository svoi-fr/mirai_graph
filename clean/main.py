import json
import copy  # Import the copy module for deep copying

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
from scripts.extract_and_add_contacts import add_contacts_to_assistant_message

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


    messages_to_keep = []
    json_lines = infile.readlines()
    for idx, line in enumerate(json_lines):
        json_obj = json.loads(line)
        user_message = json_obj["messages"][0]
        assistant_message = json_obj["messages"][1]
        content = json.loads(assistant_message['content'])
        content = rename_keys(content)
        content = remove_organizations_and_cleanup(content)
        content = add_contacts_to_assistant_message(user_message, content)
        add_null_fields(content, default_structure)
        compare_and_cleanup_urls(content)
        if content:
            propagate_city_to_contacts(content)
            match_contact_ids_to_cities(content)
            append_city_to_contact_id(content)
            add_contact_cities_to_organization(content)
            merge_contacts_within_organization(content)
            assistant_message = json.dumps(content, ensure_ascii=False)
            if content:
                messages_to_keep.append({"messages": [user_message, {"role": "assistant", "content": assistant_message}]})
            
        # # if content:
        # #     content = add_contacts_to_assistant_message(json_obj)
        # for message in json_obj['messages']:
        #     if message['role'] == 'assistant':
                
        #         content = json.loads(message['content'])
        #         content = remove_organizations_and_cleanup(content)
        #         if content:
        #             content = add_contacts_to_assistant_message(json_obj)
        #         # Perform the full processing pipeline
        #         if not content:
        #             continue
        #         rename_keys(content)
        #         # content = remove_organizations_and_cleanup(content)
                
        #         if content:
        #             # compare_and_cleanup_urls(content)
        #             # add_null_fields(content, default_structure)
        #             # propagate_city_to_contacts(content)
        #             # match_contact_ids_to_cities(content)
        #             # append_city_to_contact_id(content)
        #             # add_contact_cities_to_organization(content)
        #             # merge_contacts_within_organization(content)
                    
        #             # Ensure no circular references exist
        #             # content = copy.deepcopy(content)
                    
        #             # Convert the content back to a JSON string for the message
        #             messages_to_keep.append(json_obj)
        #             # message['content'] = json.dumps(content, ensure_ascii=False)
        
    
    total_lines = len(messages_to_keep)
    validation_lines = 50
    training_lines = total_lines - validation_lines
    for idx, line in enumerate(messages_to_keep):
        try:
            if idx < training_lines:
                json.dump(line, train_outfile, ensure_ascii=False)
                train_outfile.write('\n')
            else:
                json.dump(line, val_outfile, ensure_ascii=False)
                val_outfile.write('\n')
        except ValueError as e:
            print(f"Error serializing message at index {idx}: {e}")
            print(f"Problematic content: {json_obj}")
            

        # # Write to appropriate output file
        # try:
        #     if idx < training_lines:
        #         json.dump(json_obj, train_outfile, ensure_ascii=False)
        #         train_outfile.write('\n')
        #     else:
        #         json.dump(json_obj, val_outfile, ensure_ascii=False)
        #         val_outfile.write('\n')
        # except ValueError as e:
        #     print(f"Error serializing message at index {idx}: {e}")
        #     print(f"Problematic content: {json_obj}")

print(f"Processing complete. Training set saved as {training_output_file}, validation set saved as {validation_output_file}.")
