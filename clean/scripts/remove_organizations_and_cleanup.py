def remove_organizations_and_cleanup(content):
    # Define the organizations to be removed
    organizations_to_remove = {'qx1', 'refugies_info', 'exil_solidaire'}
    contacts_to_remove = set()
    contexts_to_remove = set()
    provisions_to_remove = set()
    tasks_to_remove = set()

    # Remove specified organizations
    if 'Organization' in content:
        for org in content['Organization']:
            if org['id'] in organizations_to_remove:
                contacts_to_remove.update(org.get('contacts', []))
                print(f"Removing organization ID '{org['id']}'")
        content['Organization'] = [
            org for org in content['Organization']
            if org['id'] not in organizations_to_remove
        ]

        for org in content['Organization']:
            org['contacts'] = [
                contact for contact in org.get('contacts', [])
                if contact not in contacts_to_remove
            ]
    
        # print(content['Organization'])
        if contacts_to_remove:
            print("Remove contacts", contacts_to_remove)

    # Remove contacts associated with removed organizations
    if 'Contact' in content:
        content['Contact'] = [
            contact for contact in content['Contact']
            if contact['id'] not in contacts_to_remove 
        ]
        print(content['Contact'])


    context_ids = set()
    # Remove Provisions that no longer have any organizations
    if 'Provision' in content:
        for provision in content['Provision']:
            if len(provision['organizations']) == 1 and provision['organizations'][0] in organizations_to_remove:
                contexts_to_remove.update(provision['contexts'])
                tasks_to_remove.update([task['id'] for task in content.get('Task', []) if provision['id'] in task.get('provisions', [])])
            provision['organizations'] = [
                org for org in provision['organizations']
                if org not in organizations_to_remove]
            
        content['Provision'] = [
            provision for provision in content['Provision']
            if provision['organizations']
        ]
        print(content['Provision'])
    
    provision_ids = {provision['id'] for provision in content.get('Provision', [])}
    context_ids.update({context_id for provision in content.get('Provision', []) for context_id in provision['contexts']})

    if 'Task' in content:
        content['Task'] = [
            task for task in content['Task']
            if task['id'] not in tasks_to_remove
        ]
        # for task in content['Task']:
            
    #         if 'provisions' in task:
    #             task['provisions'] = [
    #                 provision for provision in task['provisions']
    #                 if provision in provision_ids
    #             ]
    #     # content['Task'] = [
    #     #     task for task in content['Task']
    #     #     if task['provisions']
    #     # ]
    # task_ids = {task['id'] for task in content.get('Task', [])}
    context_ids.update({context_id for task in content.get('Task', []) for context_id in task['contexts']})

    # Remove Contexts that no longer have any Provisions
    if 'Context' in content:
        content['Context'] = [
            context for context in content['Context']
            if context['id'] in context_ids
        ]

    
    # context_ids = {context['id'] for context in content.get('Context', [])}

    # If the Summary node has a type 'directory' and there are no Contact nodes, remove the entire message
    if content.get('Summary', {}).get('type') == 'directory' and not content.get('Contact') or not content.get('Context'):
        return None

    return content
