def merge_contacts_within_organization(content):
    if 'Organization' not in content or 'Contact' not in content:
        return
    
    contact_list = content['Contact']
    contact_dict = {contact['id']: contact for contact in contact_list}
    
    for org in content['Organization']:
        if 'contacts' not in org:
            continue
        
        # Group contacts by city within this organization
        city_contact_map = {}
        for contact_id in org['contacts']:
            contact = contact_dict.get(contact_id)
            if not contact:
                continue
            city = contact.get('city')
            if not city:
                continue
            if city not in city_contact_map:
                city_contact_map[city] = []
            city_contact_map[city].append(contact)
        
        merged_contact_ids = []
        for city, contacts in city_contact_map.items():
            if len(contacts) <= 1:
                merged_contact_ids.extend([contact['id'] for contact in contacts])
                continue
            
            merged_contact = {
                'id': min(contact['id'] for contact in contacts),
                'city': city,
                'address': None,
                'phone': None,
                'email': None,
                'contact_page': None
            }
            
            for contact in contacts:
                for field in ['address', 'phone', 'email', 'contact_page']:
                    if contact[field]:
                        merged_contact[field] = contact[field]
            
            merged_contact_ids.append(merged_contact['id'])
            
            # Remove old contacts and add the new merged contact
            for contact in contacts:
                if contact['id'] != merged_contact['id']:
                    print(f"Merging contact ID '{contact['id']}' into '{merged_contact['id']}'")
                    contact_list.remove(contact)
            contact_list.append(merged_contact)
        
        # Update the organization's contacts list with the merged contact IDs
        org['contacts'] = list(set(merged_contact_ids))
