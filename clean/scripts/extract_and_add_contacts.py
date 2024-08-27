import re
import json
from collections import defaultdict
from .remove_organizations_and_cleanup import remove_organizations_and_cleanup

def extract_addresses_from_text(text):
    # Regex to specifically capture addresses following "#### Address" format with Marseille
    specific_address_regex = r'####\s*Address\s*\n([\w\s\-\.\,]+,\sMarseille,\sFrance)'
    specific_addresses = re.findall(specific_address_regex, text)

    # Regex to capture general addresses with a 5-digit postal code and city
    general_address_regex = r'(?<=\n)[\w\s\-\.\,]*\d{5}\s[\w\s\-]+,\sFrance'
    general_addresses = re.findall(general_address_regex, text)
    
    # Combine the addresses found by both regex patterns
    all_addresses = specific_addresses + general_addresses
    
    # Clean up any newlines or extra spaces in the extracted addresses
    cleaned_addresses = [re.sub(r'\s+', ' ', address).strip() for address in all_addresses]
    
    # Debug print to see what addresses were captured
    if cleaned_addresses:
        print("Captured addresses:", cleaned_addresses)
    return cleaned_addresses

def extract_phone_numbers_from_text(text):
    phone_regex = r'(?:\+33|0|\+33\s\(0\))\s?\d{1}(?:\s?\d{2}){4}'
    phone_numbers = re.findall(phone_regex, text)
    return phone_numbers

def extract_emails_from_text(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_regex, text)
    return emails

def generate_contact_id(org_id, city, existing_count):
    city_normalized = normalize_city_name(city)
    if existing_count > 1:
        contact_id = f"contact_{org_id}_{city_normalized}_{existing_count}"
    else:
        contact_id = f"contact_{org_id}_{city_normalized}"
    return contact_id

def normalize_city_name(city):
    return city.lower().replace(' ', '_').replace('-', '_')

def extract_city_from_address(address):
    # If the address is in the specific format for Marseille, return Marseille as the city
    if ", Marseille, France" in address:
        return "Marseille"
    
    # Extract the city name from a general address, which should be the part after the postal code and before ", France"
    city_regex = r'\d{5}\s([\w\s\-]+),\sFrance'
    match = re.search(city_regex, address)
    if match:
        return match.group(1).strip()
    return None

def add_contacts_to_assistant_message(user_message, content):
    if not content:
        return None
    user_text = user_message['content']
    addresses = extract_addresses_from_text(user_text)
    phone_numbers = extract_phone_numbers_from_text(user_text)
    emails = extract_emails_from_text(user_text)
    
    if addresses:
        if 'Organization' in content:
            contact_list = content.get('Contact', [])
            for org in content['Organization']:
                org_id = org['id']
                city_contact_count = defaultdict(int)
                existing_contacts = {contact['city']: contact for contact in contact_list if contact.get('city')}
                print(contact_list)
                print(existing_contacts)

                filled_new = False
                for i, address in enumerate(addresses):
                    city = extract_city_from_address(address)
                    if not city:
                        print(f"Could not extract a valid city from address: {address}")
                        continue

                    if 'cities' not in org:
                        org['cities'] = [city]
                    elif city not in org['cities']:
                        org['cities'].append(city)

                    # Count how many contacts exist for this city
                    city_contact_count[city] += 1
                    print(existing_contacts)
                    contact = None
                    if not filled_new:
                        if len(contact_list) == 1:
                            contact = contact_list[0]
                        elif city in existing_contacts:
                            contact = existing_contacts[city]
                        else:
                            city_normalized = normalize_city_name(city)
                            for norm_contact in contact_list:
                                if norm_contact['id'].endswith(city_normalized):
                                    contact = norm_contact
                                    break

                        

                    # Update existing contact for the city if it exists and doesn't have an address
                    if contact:
                        if not contact.get('address'):
                            contact['address'] = address
                        if not contact.get('city'):
                            contact['city'] = city
                        if not contact.get('phone') and phone_numbers:
                            contact['phone'] = phone_numbers[i] if i < len(phone_numbers) else None
                        if not contact.get('email') and emails:
                            contact['email'] = emails[i] if i < len(emails) else None
                        print(f"Updated existing contact ID '{contact['id']}' with address '{address}'")
                    else:
                        if address not in [contact.get('address') for contact in contact_list]:
                            # No existing contact for this city or existing contact already has an address, create a new contact node
                            contact_id = generate_contact_id(org_id, city, city_contact_count[city])
                            contact_node = {
                                'id': contact_id,
                                'address': address,
                                'city': city,
                                'phone': phone_numbers[i] if i < len(phone_numbers) else None,
                                'email': emails[i] if i < len(emails) else None,
                                'contact_page': None
                            }
                            contact_list.append(contact_node)
                            print(f"Added new contact ID '{contact_id}' with address '{address}' to organization ID '{org_id}'")
                            filled_new = True
                
                content['Contact'] = contact_list


                # Optional: Assign phone and email to existing contacts if they are still missing
                # Only if there is one organization and one contact
                if len(contact_list) == 1 and len(content['Organization']) == 1:
                    contact = contact_list[0]
                    if not contact.get('phone') and phone_numbers:
                        contact['phone'] = phone_numbers[0]
                    if not contact.get('email') and emails:
                        contact['email'] = emails[0]
                id_list = set()
                
                for contact in contact_list:
                    if contact['id'] in id_list:
                        contact_list.remove(contact)
                    id_list.add(contact['id'])

        # Update the assistant message with the modified content
        return content
    return content 
