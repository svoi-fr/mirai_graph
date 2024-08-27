def rename_keys(content):
    # Rename 'url' to 'website' in 'Organization'
    if 'Organization' in content:
        for org in content['Organization']:
            if 'url' in org:
                print(f"Renaming 'url' to 'website' for organization ID '{org['id']}'")
                org['website'] = org.pop('url')

    # Rename 'url' to 'contact_page' in 'Contact'
    if 'Contact' in content:
        for contact in content['Contact']:
            if 'url' in contact:
                print(f"Renaming 'url' to 'contact_page' for contact ID '{contact['id']}'")
                contact['contact_page'] = contact.pop('url')
    if 'Task' in content:
        content['Task'] = [task for task in content['Task'] if 'url' not in task]
    return content
