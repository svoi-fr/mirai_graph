import json
import unicodedata

def add_null_fields(obj, default_structure):
    if isinstance(obj, dict):
        for key, value in default_structure.items():
            if key not in obj:
                obj[key] = [] if isinstance(value, list) else value
            elif isinstance(value, dict):
                if not isinstance(obj.get(key), dict):
                    obj[key] = value
                else:
                    add_null_fields(obj[key], value)
            elif isinstance(value, list):
                if not isinstance(obj.get(key), list):
                    obj[key] = []
                elif len(value) > 0 and isinstance(value[0], dict):
                    for item in obj[key]:
                        add_null_fields(item, value[0])
    elif isinstance(obj, list):
        for item in obj:
            add_null_fields(item, default_structure[0])

def normalize_city_name(city):
    city_normalized = unicodedata.normalize('NFKD', city).encode('ascii', 'ignore').decode('ascii')
    city_normalized = city_normalized.lower().replace(' ', '_')
    return city_normalized

def propagate_city_to_contacts(content):
    org_city_mapping = {}
    
    if "Organization" in content:
        for org in content["Organization"]:
            if len(org.get("cities", [])) == 1:
                org_city_mapping[org["id"]] = org["cities"][0]
    
    if "Contact" in content:
        for contact in content["Contact"]:
            if not contact.get("city") and contact.get("id"):
                for org in content.get("Organization", []):
                    if contact["id"] in org.get("contacts", []) and org["id"] in org_city_mapping:
                        contact["city"] = org_city_mapping[org["id"]]
                        print(f"Added city '{contact['city']}' to contact ID '{contact['id']}'")
                        break

def match_contact_ids_to_cities(content):
    if "Organization" not in content or "Contact" not in content:
        return

    for org in content["Organization"]:
        cities = org.get("cities", [])
        if not cities:
            continue

        for contact in content["Contact"]:
            if not contact.get("city") and contact.get("id"):
                normalized_id = normalize_city_name(contact["id"])
                for city in cities:
                    normalized_city = normalize_city_name(city)
                    if normalized_city in normalized_id:
                        contact["city"] = city
                        print(f"Matched city '{city}' to contact ID '{contact['id']}'")
                        break

def append_city_to_contact_id(content):
    contact_id_mapping = {}
    
    if "Contact" in content:
        for contact in content["Contact"]:
            if contact.get("city"):
                normalized_city = normalize_city_name(contact["city"])
                if normalized_city not in contact["id"]:
                    new_contact_id = f"{contact['id']}_{normalized_city}"
                    contact_id_mapping[contact["id"]] = new_contact_id
                    contact["id"] = new_contact_id
                    print(f"Appended city '{contact['city']}' to contact ID, new ID: '{new_contact_id}'")
                else:
                    print(f"City '{contact['city']}' already in contact ID '{contact['id']}', skipping append.")
    
    if "Organization" in content:
        for org in content["Organization"]:
            updated_contacts = []
            for contact_id in org.get("contacts", []):
                updated_contacts.append(contact_id_mapping.get(contact_id, contact_id))
            org["contacts"] = updated_contacts

def merge_contacts_within_organization(content):
    if "Organization" not in content or "Contact" not in content:
        return
    
    contact_list = content["Contact"]
    contact_dict = {contact["id"]: contact for contact in contact_list}
    
    for org in content["Organization"]:
        if "contacts" not in org:
            continue
        
        # Group contacts by city within this organization
        city_contact_map = {}
        for contact_id in org["contacts"]:
            contact = contact_dict.get(contact_id)
            if not contact:
                continue
            city = contact.get("city")
            if not city:
                continue
            if city not in city_contact_map:
                city_contact_map[city] = []
            city_contact_map[city].append(contact)
        
        merged_contact_ids = []
        for city, contacts in city_contact_map.items():
            if len(contacts) <= 1:
                merged_contact_ids.extend([contact["id"] for contact in contacts])
                continue
            
            merged_contact = {
                "id": min(contact["id"] for contact in contacts),
                "city": city,
                "address": None,
                "phone": None,
                "email": None,
                "url": None
            }
            
            for contact in contacts:
                for field in ["address", "phone", "email", "url"]:
                    if contact[field]:
                        merged_contact[field] = contact[field]
            
            merged_contact_ids.append(merged_contact["id"])
            
            # Remove old contacts and add the new merged contact
            for contact in contacts:
                if contact["id"] != merged_contact["id"]:
                    print(f"Merging contact ID '{contact['id']}' into '{merged_contact['id']}'")
                    contact_list.remove(contact)
            contact_list.append(merged_contact)
        
        # Update the organization's contacts list with the merged contact IDs
        org["contacts"] = list(set(merged_contact_ids))

def add_contact_cities_to_organization(content):
    if "Organization" not in content or "Contact" not in content:
        return

    for org in content["Organization"]:
        existing_cities = set(org.get("cities", []))
        
        # Collect cities from the associated contacts
        for contact_id in org.get("contacts", []):
            for contact in content["Contact"]:
                if contact["id"] == contact_id and contact.get("city"):
                    existing_cities.add(contact["city"])
        
        if existing_cities:
            org["cities"] = list(existing_cities)
            print(f"Updated cities for organization ID '{org['id']}': {org['cities']}")

# Define the complete default structure based on your provided schema
default_structure = {
    "Summary": {
        "id": None,
        "info": None,
        "country": None,
        "cities": [],
        "type": None
    },
    "Organization": [
        {
            "id": None,
            "info": None,
            "contacts": [],
            "url": None,
            "cities": []
        }
    ],
    "Provision": [
        {
            "id": None,
            "info": None,
            "contexts": [],
            "organizations": []
        }
    ],
    "Contact": [
        {
            "id": None,
            "address": None,
            "city": None,
            "phone": None,
            "email": None,
            "url": None
        }
    ],
    "Context": [
        {
            "id": None,
            "info": None
        }
    ],
    "Task": [
        {
            "id": None,
            "info": None,
            "contexts": [],
            "provisions": []
        }
    ]
}

# Input and output file paths
input_file = 'output.jsonl'
output_file = 'outputs_with_nulls.jsonl'

# Process the JSONL file
with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        json_obj = json.loads(line)
        for message in json_obj["messages"]:
            if message["role"] == "assistant":
                content = json.loads(message["content"])
                add_null_fields(content, default_structure)
                propagate_city_to_contacts(content)
                match_contact_ids_to_cities(content)
                append_city_to_contact_id(content)
                add_contact_cities_to_organization(content)
                merge_contacts_within_organization(content)
                message["content"] = json.dumps(content, ensure_ascii=False)
        json.dump(json_obj, outfile, ensure_ascii=False)
        outfile.write('\n')

print(f"Processing complete. Updated file saved as {output_file}.")
