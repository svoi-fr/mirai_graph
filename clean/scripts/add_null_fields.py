def add_null_fields(obj, default_structure):
    if isinstance(obj, dict):
        for key, value in default_structure.items():
            if key not in obj:
                obj[key] = [] if isinstance(value, list) else value
            elif isinstance(value, dict):
                if not isinstance(obj.get(key), dict):
                    obj[key] = value
                else:
                    add_null_fields(obj[key], value)
            elif isinstance(value, list):
                if not isinstance(obj.get(key), list):
                    obj[key] = []
                elif len(value) > 0 and isinstance(value[0], dict):
                    for item in obj[key]:
                        add_null_fields(item, value[0])
    elif isinstance(obj, list):
        for item in obj:
            add_null_fields(item, default_structure[0])
