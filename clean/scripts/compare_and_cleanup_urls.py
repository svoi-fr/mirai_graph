from urllib.parse import urlparse

def is_top_level_url(url):
    parsed_url = urlparse(url)
    return not parsed_url.path or parsed_url.path == '/'

def compare_and_cleanup_urls(content):
    if 'Organization' in content and 'Contact' in content:
        for org in content['Organization']:
            org_website = org.get('website')
            if not org_website:
                continue
            
            for contact in content['Contact']:
                contact_page = contact.get('contact_page')
                if not contact_page:
                    continue
                
                if org_website == contact_page:
                    if is_top_level_url(contact_page):
                        # Remove contact_page from the contact node
                        contact.pop('contact_page')
                        print(f"Removed top-level URL from contact ID '{contact['id']}'")
                    else:
                        # Remove website from the organization node
                        org.pop('website')
                        print(f"Removed non top-level URL from organization ID '{org['id']}'")
                    break
