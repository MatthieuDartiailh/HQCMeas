"""
"""
completer_tooltip = """In this field you can enter a text and include
                      fields which will be replaced by database
                      entries by using the delimiters '{' and '}'."""

def get_formatted_string(edit_str, path, database):
    """
    """
    aux_strings = edit_str.split('{')
    string_elements = [ string for aux in aux_strings
                                for string in aux.split('}')]

    replacement_values = [database.get_value(path, key)
                        for key in string_elements[1::2]]
    str_to_format = ''
    for key in string_elements[::2]:
        str_to_format += key + '_{}_'

    if edit_str.endswith('}'):
        str_to_format = edit_str[:-5]
    else:
        str_to_format = edit_str[:-4]


    return str_to_format.format(*replacement_values)