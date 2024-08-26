def propagate_city_to_contacts(content):
    org_city_mapping = {}
    
    if 'Organization' in content:
        for org in content['Organization']:
            if len(org.get('cities', [])) == 1:
                org_city_mapping[org['id']] = org['cities'][0]
    
    if 'Contact' in content:
        for contact in content['Contact']:
            if not contact.get('city') and contact.get('id'):
                for org in content.get('Organization', []):
                    if contact['id'] in org.get('contacts', []) and org['id'] in org_city_mapping:
                        contact['city'] = org_city_mapping[org['id']]
                        print(f"Added city '{contact['city']}' to contact ID '{contact['id']}'")
                        break
