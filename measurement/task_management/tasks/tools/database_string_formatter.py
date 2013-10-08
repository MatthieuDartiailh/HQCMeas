"""
"""
import textwrap
COMPLETER_TOOLTIP = textwrap.fill("""In this field you can enter a text and
                        include fields which will be replaced by database
                        entries by using the delimiters '{' and '}'.""", 80)

def get_formatted_string(edit_str, path, database):
    """
    """
    aux_strings = edit_str.split('{')
    if len(aux_strings) > 1:
        string_elements = [ string for aux in aux_strings
                                    for string in aux.split('}')]
        replacement_values = [database.get_value(path, key)
                            for key in string_elements[1::2]]
        str_to_format = ''
        for key in string_elements[::2]:
            str_to_format += key + '{}'
        if edit_str.endswith('}'):
            str_to_format = str_to_format[:-2]
        else:
            str_to_format = str_to_format[:-2]
    
        return str_to_format.format(*replacement_values)
    else:
        return edit_str