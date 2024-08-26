def add_contact_cities_to_organization(content):
    if 'Organization' not in content or 'Contact' not in content:
        return

    for org in content['Organization']:
        existing_cities = set(org.get('cities', []))
        
        # Collect cities from the associated contacts
        for contact_id in org.get('contacts', []):
            for contact in content['Contact']:
                if contact['id'] == contact_id and contact.get('city'):
                    existing_cities.add(contact['city'])
        
        if existing_cities:
            org['cities'] = list(existing_cities)
            print(f"Updated cities for organization ID '{org['id']}': {org['cities']}")
