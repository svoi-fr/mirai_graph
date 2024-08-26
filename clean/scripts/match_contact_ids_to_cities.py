from .normalize_city_name import normalize_city_name

def match_contact_ids_to_cities(content):
    if 'Organization' not in content or 'Contact' not in content:
        return

    for org in content['Organization']:
        cities = org.get('cities', [])
        if not cities:
            continue

        for contact in content['Contact']:
            if not contact.get('city') and contact.get('id'):
                normalized_id = normalize_city_name(contact['id'])
                for city in cities:
                    normalized_city = normalize_city_name(city)
                    if normalized_city in normalized_id:
                        contact['city'] = city
                        print(f"Matched city '{city}' to contact ID '{contact['id']}'")
                        break
