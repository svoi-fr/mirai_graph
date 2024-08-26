from .normalize_city_name import normalize_city_name

def append_city_to_contact_id(content):
    contact_id_mapping = {}
    
    if 'Contact' in content:
        for contact in content['Contact']:
            if contact.get('city'):
                normalized_city = normalize_city_name(contact['city'])
                if normalized_city not in contact['id']:
                    new_contact_id = f"{contact['id']}_{normalized_city}"
                    contact_id_mapping[contact['id']] = new_contact_id
                    contact['id'] = new_contact_id
                    print(f"Appended city '{contact['city']}' to contact ID, new ID: '{new_contact_id}'")
                else:
                    print(f"City '{contact['city']}' already in contact ID '{contact['id']}', skipping append.")
    
    if 'Organization' in content:
        for org in content['Organization']:
            updated_contacts = []
            for contact_id in org.get('contacts', []):
                updated_contacts.append(contact_id_mapping.get(contact_id, contact_id))
            org['contacts'] = updated_contacts
