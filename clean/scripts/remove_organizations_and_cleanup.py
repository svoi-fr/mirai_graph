import json
def remove_organizations_and_cleanup(content):
    orgs_to_remove = {'qx1', 'refugies_info', 'exil_solidaire'}
    
    # Debug: Print the initial content for inspection

    # Remove specified organizations
    if 'Organization' in content:
        original_org_count = len(content['Organization'])
        content['Organization'] = [org for org in content['Organization'] if org['id'] not in orgs_to_remove]

    # Remove contacts that belong to deleted organizations
    if 'Contact' in content:
        all_referenced_contacts = {contact_id for org in content['Organization'] for contact_id in org.get('contacts', [])}
        original_contact_count = len(content['Contact'])
        content['Contact'] = [contact for contact in content['Contact'] if contact['id'] in all_referenced_contacts]

    # Remove references to the deleted organizations in Provisions and remove empty Provisions
    if 'Provision' in content:
        new_provisions = []
        for provision in content['Provision']:
            # Remove references to organizations to be deleted
            provision['organizations'] = [org_id for org_id in provision.get('organizations', []) if org_id not in orgs_to_remove]
            # If the provision still has organizations, keep it
            if provision['organizations']:
                new_provisions.append(provision)
        content['Provision'] = new_provisions

    # Remove Tasks that no longer have contexts or provisions
    if 'Task' in content:
        new_tasks = []
        for task in content['Task']:
            # Ensure both contexts and provisions exist
            if task.get('contexts') and task.get('provisions'):
                new_tasks.append(task)
        content['Task'] = new_tasks
    
    # Remove Contexts that are no longer referenced by any Task or Provision
    if 'Context' in content:
        referenced_contexts = set()
        if 'Task' in content:
            for task in content['Task']:
                referenced_contexts.update(task.get('contexts', []))
        if 'Provision' in content:
            for provision in content['Provision']:
                referenced_contexts.update(provision.get('contexts', []))
        original_context_count = len(content['Context'])
        content['Context'] = [context for context in content['Context'] if context['id'] in referenced_contexts]
    
    # If no contexts left, remove the entire user/system pair
    if 'Context' in content and not content['Context']:
        return None

    # Delete content if there are no Provisions or Tasks left
    if not content.get('Provision') and not content.get('Task'):
        return None
    
    # Delete content if Summary:type is "directory" and there are no Contact nodes
    if content.get('Summary', {}).get('type') == 'directory' and not content.get('Contact'):
        return None

    # Debug: Print the final content after cleanup

    return content
