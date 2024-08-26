from urllib.parse import urlparse
import requests
import os

def load_valid_urls():
    valid_urls = set()
    if os.path.exists("valid_url.txt"):
        with open("valid_url.txt", "r") as file:
            for line in file:
                valid_urls.add(line.strip())
    return valid_urls

def save_valid_url(url):
    with open("valid_url.txt", "a") as file:
        file.write(url + "\n")

def is_valid_url(url, valid_urls):
    if url in valid_urls:
        return True
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        response = requests.get(url, allow_redirects=True, timeout=10)  # Switched to GET request
        if response.status_code == 200:
            save_valid_url(url)
            valid_urls.add(url)
            return True
        return False
    except (requests.RequestException, ValueError) as e:
        # Log the error but assume the URL might be good if it's well-formed
        print(f"Error validating URL {url}: {e}")
        return parsed_url.scheme in ["http", "https"] and bool(parsed_url.netloc)

def is_domain_to_nullify(url):
    domains_to_nullify = ['refugies.info', 'exil-solidaire.fr', 'qx1.org']
    parsed_url = urlparse(url)
    return parsed_url.netloc in domains_to_nullify  # Only nullify exactly these domains

def is_top_level_url(url):
    parsed_url = urlparse(url)
    return not parsed_url.path or parsed_url.path == '/'

def compare_and_cleanup_urls(content):
    # Load cached valid URLs
    valid_urls = load_valid_urls()

    # Nullify or remove invalid or unwanted URLs in Organization
    if 'Organization' in content:
        for org in content['Organization']:
            # Set cities to empty array for specified organization IDs
            if org['id'] in ['cnda', 'ofpra', 'spada', 'prefecture', 'mairie']:
                print(f"Setting cities to empty array for organization {org['id']}")
                org['cities'] = []

            website = org.get('website')
            if website:
                if is_domain_to_nullify(website) or not is_valid_url(website, valid_urls):
                    print(f"Nullifying website for organization {org['id']}: {website}")
                    org['website'] = None
                elif not is_top_level_url(website):
                    print(f"Removing non-top-level URL from organization {org['id']}: {website}")
                    org['website'] = None

    # Nullify or remove invalid or unwanted URLs in Contact
    if 'Contact' in content:
        contacts_to_remove = []
        for contact in content['Contact']:
            # Nullify the email if it is 'contact@qx1.org'
            if contact.get('email') == 'contact@qx1.org':
                print(f"Nullifying email for contact {contact['id']}: {contact['email']}")
                contact['email'] = None

            contact_page = contact.get('contact_page')
            if contact_page:
                if is_domain_to_nullify(contact_page) or not is_valid_url(contact_page, valid_urls):
                    print(f"Nullifying contact_page for contact {contact['id']}: {contact_page}")
                    contact['contact_page'] = None

            # Remove the contact if no fields are left after the cleanup
            if all(value is None for key, value in contact.items() if key != 'id'):
                print(f"Removing contact {contact['id']} because it has no other fields.")
                contacts_to_remove.append(contact)
        
        for contact in contacts_to_remove:
            content['Contact'].remove(contact)
            for org in content.get('Organization', []):
                if contact['id'] in org.get('contacts', []):
                    org['contacts'].remove(contact['id'])

    # Move top-level contact_page to Organization and remove empty Contacts
    if 'Organization' in content and 'Contact' in content:
        for org in content['Organization']:
            for contact in content['Contact']:
                contact_page = contact.get('contact_page')
                if contact_page and is_top_level_url(contact_page):
                    if not org.get('website'):
                        org['website'] = contact_page
                        print(f"Moved top-level URL from contact {contact['id']} to organization {org['id']}")
                    contact['contact_page'] = None

                # Remove the contact if no fields are left after the cleanup
                if all(value is None for key, value in contact.items() if key != 'id' and key != 'city'):
                    if 'contacts' in org and contact['id'] in org['contacts']:
                        org['contacts'].remove(contact['id'])
                    print(f"Removed contact {contact['id']} because it had no other fields.")
                    content['Contact'].remove(contact)
