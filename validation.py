def prune_empty_and_invalid_references(data):
    def get_referenced_ids(node_list, key):
        return set(ref for node in node_list for ref in node.get(key, []))

    context_ids = set(node.get("id") for node in data.get("Context", []))
    provision_ids = set(node.get("id") for node in data.get("Provision", []))
    task_ids = set(node.get("id") for node in data.get("Task", []))
    organization_ids = set(node.get("id") for node in data.get("Organization", []))
    contact_ids = set(node.get("id") for node in data.get("Contact", []))

    for node_type in ["Context", "Provision", "Task", "Organization", "Contact"]:
        for node in data.get(node_type, []):
            for key, value in list(node.items()):
                if key in ("context", "provision", "organization", "contact"):
                    if isinstance(value, str):
                        value = [value] 
                    # Correct variable names in list comprehension:
                    valid_refs = [ref for ref in value if ref in locals()[key[:-1] + "_ids"]] # Remove the 's'
                    if valid_refs:
                        node[key] = valid_refs
                    else:
                        del node[key]
                elif value in ([], "", None):
                    del node[key]

        if not data.get(node_type, []) and node_type in data:
            del data[node_type]

    return data

def validate_and_prune_json(data):
    errors = []  # Collect all validation errors

    if "Summary" not in data:
        errors.append("Output must have a Summary node.")

    if "Context" not in data or not data["Context"]:
        errors.append("Output should have at least one Context node.")

    for node_type in ["Context", "Provision", "Task", "Organization", "Contact"]:
      for node in data.get(node_type, []):
          if "id" not in node:
              errors.append(f"{node_type} node is missing the 'id' field: {node}")
          if node_type != "Contact" and "info" not in node:
              errors.append(f"{node_type} node with ID '{node.get('id', 'unknown')}' is missing the 'info' field: {node}")
    def get_referenced_context_ids(node_list):
        return set(ref for node in node_list for ref in node.get("contexts", []))

    def get_referenced_organization_ids(node_list):
        return set(ref for node in node_list for ref in node.get("organizations", []))

    def get_referenced_provision_ids(node_list):
        return set(ref for node in node_list for ref in node.get("provision", []))

    def get_referenced_contact_ids(node_list):
        return set(ref for node in node_list for ref in node.get("contacts", [])) if isinstance(node_list, list) else {node_list}

    referenced_context_ids = get_referenced_context_ids(data.get("Provision", [])) | get_referenced_context_ids(data.get("Task", []))
    for context in data.get("Context", []):
        if context["id"] not in referenced_context_ids:
            errors.append(f"Context node {context['id']} is not referenced by any other node - link existing Task or Provision to it, create Task or Provision or delete Context.")

    referenced_organization_ids = get_referenced_organization_ids(data.get("Provision", []))
    for organization in data.get("Organization", []):
        if organization["id"] not in referenced_organization_ids:
            errors.append(f"Organization node {organization['id']} is not referenced by any Provision nodes - add Provisions or remove Organization.")

    referenced_provision_ids = get_referenced_provision_ids(data.get("Task", [])) | get_referenced_provision_ids(data.get("Organization", []))
    # for provision in data.get("Provision", []):
    #     if provision["id"] not in referenced_provision_ids:
    #         errors.append(f"Provision node {provision['id']} is not referenced by any other node.")

    referenced_contact_ids = get_referenced_contact_ids(data.get("Organization", [])) | get_referenced_contact_ids(data.get("Task", []))
    for contact in data.get("Contact", []):
        if contact["id"] not in referenced_contact_ids:
            errors.append(f"Contact node {contact['id']} is not referenced by any other node - add an Organization connection or remove contact.")

    for provision in data.get("Provision", []):
        if not provision.get("organizations"):
            errors.append(f"Provision node {provision['id']} must be linked to at least one Organization node - convert to Task node if it can't be linked, or link to an Organization that provides it")
        if not provision.get("contexts"):
            errors.append(f"Provision node {provision['id']} must be linked to at least one Context node.")

    for task in data.get("Task", []):
        if not task.get("contexts"):
            errors.append(f"Task node {task['id']} must be linked to at least one Context node.")

    for contact in data.get("Contact", []):
        if "address" in contact and "city" not in contact:
            errors.append(f"Contact node {contact['id']} has 'address' but no 'city' defined.")

    # --- Pruning Step for "directory" type ---
    if "Summary" in data and data["Summary"].get("type") == "directory":
        # Remove all Task nodes
        if "Task" in data:
          del data["Task"]

        # Get Context IDs referenced by Provisions
        provision_context_ids = set(ref for provision in data.get("Provision", []) for ref in provision.get("contexts", []))

        # Remove Contexts only linked to Tasks (and not Provisions)
        data["Context"] = [c for c in data.get("Context", []) if c["id"] in provision_context_ids]

        if len(data.get("Contact", [])) == 0:
            errors.append("Directory article type must have at least one Contact node.")
        if len(data.get("Organization", [])) == 0:
            errors.append("Directory article type must have at least one Organization node.")
        if len(data.get("Provision", [])) == 0:
            errors.append("Directory article type must have at least one Provision node.")



    return errors  # Return the list of errors
