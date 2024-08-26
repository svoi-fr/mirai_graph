def rename_keys(content):
    # Rename 'url' to 'website' in 'Organization'
    if 'Organization' in content:
        for org in content['Organization']:
            if 'url' in org:
                org['website'] = org.pop('url')
    
    # Rename 'url' to 'contact_page' in 'Contact'
    if 'Contact' in content:
        for contact in content['Contact']:
            if 'url' in contact:
                contact['contact_page'] = contact.pop('url')
