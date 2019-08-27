basic_types = [int, float, complex, range, str, bytes, bytearray, memoryview, set, frozenset, dict]

def is_basic_type (obj):
    for basic_type in basic_types:
        if isinstance (obj, basic_type):
            return True
    return False

def format_iterable (iter, format_str):
    return format_str.format (", ".join ([print_object (iter_item) for iter_item in iter]))

def print_object (obj):
    if is_basic_type (obj):
        return str (obj)
    if isinstance (obj, list):
        return format_iterable (obj, "[{}]")
    if isinstance (obj, tuple):
        return format_iterable (obj, "({})")
    obj_attr_names = dir (obj)
    out_attrs = []
    for obj_attr_name in obj_attr_names:
        if obj_attr_name.startswith ("__") and obj_attr_name.endswith ("__"):
            # out_attrs.append ("{0}: (special)".format (obj_attr_name))
            # (this adds spam since all objects have a ton of these)
            pass
        else:
            if hasattr (obj, obj_attr_name):
                obj_attr = getattr (obj, obj_attr_name)
                if obj_attr is obj:
                    obj_attr_as_string = "(self)"
                elif is_basic_type (obj_attr):
                    obj_attr_as_string = str (obj_attr)
                else:
                    obj_attr_as_string = print_object (obj_attr)
                out_attr = "{0}: {1}".format (obj_attr_name, obj_attr_as_string)
                out_attrs.append (out_attr)
            else:
                pass
    out_string = ', '.join (out_attrs)
    return out_string
