"""
    Document module should create dynamic class from template with some default methods
    which I want to have option do on fields.
"""
# TODO: Refactorize this file?

from typing import (
    MutableMapping,
    Mapping
)

def make_template_dict(original_dict: Mapping,
                       template_dict: MutableMapping) -> MutableMapping:
    """
        On the basis of template_dict creates new version of original_dict.
        New dict contains only keys from template and values are taken from original_dict.
    """
    new_dict: MutableMapping = dict()
    for key, value in original_dict.items():
        if key in template_dict:
            new_dict[key] = value
            if isinstance(value, Mapping):
                new_value_keys = template_dict[key]
                new_value = make_template_dict(value, new_value_keys)
                if new_value:
                    new_dict[key] = new_value
        elif isinstance(value, Mapping):
            new_value = make_template_dict(value, template_dict)
            if new_value:
                new_dict[key] = new_value
    return new_dict

def test_correctness(template: Mapping, shortcutted: Mapping):
    """
        Special test for monitoring. If something change in original json,
        we want to know about it.
    """
    for key in template.keys():
        try:
            if shortcutted[key] != shortcutted[key]:
                raise KeyError
        except KeyError:
            return False
    return True
