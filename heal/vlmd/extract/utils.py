"""Extract utilities/helper functions"""

import re
from collections.abc import MutableMapping

import jsonschema
import pandas as pd
from pandas.api.types import is_object_dtype


def _get_prop_names_to_rearrange(prop_names, schema):
    """
    Get data dictionary props to search for refactoring or embedding

    Supports patternProperties
    """

    annotation_names = ["title", "description", "name", "additionalDescription"]
    root_names = flatten_properties(schema["properties"]).keys()
    field_names = flatten_properties(
        schema["properties"]["fields"]["items"]["properties"]
    ).keys()
    props_to_rearrange = (
        set(root_names).intersection(field_names).difference(annotation_names)
    )

    prop_names_exp = "|".join("^" + name + "$" for name in props_to_rearrange)
    names_to_rearrange = [name for name in prop_names if re.match(prop_names_exp, name)]

    return list(names_to_rearrange)


def embed_data_dictionary_props(flat_fields, flat_root, schema):
    """
    Embed (flattened) root level props in each (flattened) field
    if field level prop is missing but the field level prop exists
    and is not an annotation property (title,description).

    Args

        flat_fields: array of dicts or pd.DataFrame (or something that can be converted into DataFrame)
        flat_root: dict or pd.Series or something that can be converted into Series
        schema: schema for determining what fields should be embedded (note, this is flattened in fxn)

    Returns

        pd.DataFrame with the flat fields with the embedded root properties
    """
    flat_fields = pd.DataFrame(flat_fields)
    prop_names = _get_prop_names_to_rearrange(list(flat_root.keys()), schema)
    flat_root = pd.Series(flat_root).loc[prop_names]  # take out annotation props
    if len(flat_root) > 0:
        for prop_name in prop_names:
            if prop_name in flat_root:
                if prop_name not in flat_fields:
                    flat_fields.insert(0, prop_name, flat_root[prop_name])
                else:
                    flat_fields[prop_name].fillna(flat_root[prop_name], inplace=True)

    return flat_fields


def refactor_field_props(flat_fields, schema):
    """
    Given a flattened array of dicts corresponding to the unflattened schema,
    move up (ie `refactor`) flattened properties that are both in the root
    (ie table level; level up from field records) and in the fields.
    """
    flat_fields_df = pd.DataFrame(flat_fields)
    props = set(_get_prop_names_to_rearrange(flat_fields_df.columns.tolist(), schema))
    flat_record = pd.Series(dtype="object")
    for name in props:
        in_df = name in flat_fields_df
        if in_df:
            is_one_unique = None
            # need to handle if some values are pandas series
            if isinstance(flat_fields_df[name], pd.DataFrame):
                is_one_unique = (flat_fields_df[name].nunique() == 1).all()
            elif isinstance(flat_fields_df[name], pd.Series):
                if is_object_dtype(flat_fields_df[name]):
                    is_one_unique = len(flat_fields_df[name].map(str).unique()) == 1
                else:
                    is_one_unique = flat_fields_df[name].nunique() == 1
            if is_one_unique:
                flat_record[name] = flat_fields_df.pop(name).iloc[0]
                if isinstance(flat_record[name], pd.Series):
                    flat_record[name] = flat_record[name].to_list()

    return flat_record, flat_fields_df


# individual cell utilities
def strip_html(html_string):
    """Strip out html from string"""
    if html_string:
        return re.sub(r"<[^>]+>", "", html_string)
    else:
        return html_string


def parse_dictionary_str(string, item_sep, key_val_sep):
    """
    Parses a stringified dictionary into a dictionary
    based on item separator
    """
    if string != "" and string is not None:
        str_items = string.strip().split(item_sep)
        items = {}

        for str_item in str_items:
            if str_item:
                item = str_item.split(key_val_sep, 1)
                items[item[0].strip()] = item[1].strip()

        return items
    else:
        return string


def parse_list_str(string, item_sep):
    """Split a string into list using 'item_sep'"""
    if string != "" and string is not None:
        return string.strip().split(item_sep)
    else:
        return string


# dictionary utilities
def flatten_to_json_path(dictionary, schema, parent_key=False, sep="."):
    """
    Turn a nested dictionary into a flattened dictionary (but see schema param)

    :param dictionary: The dictionary to flatten
    :param schema: The schema to indicate which properties to flatten
        This includes dictionaries (properties) with child dictionaries (properties)
        and lists (items) with child dictionaries (properties)
    :param parent_key: The string to prepend to dictionary's keys
    :param sep: The string used to separate flattened keys
    :return: A flattened dictionary
    """
    # flatten if type array -> type object with properties
    # flatten if type object with properties
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + sep + key if parent_key else key
        try:
            prop = schema["properties"]
        except:
            message = f"Missing key: 'properties' in prop {prop}"
            raise KeyError(message)
        prop = schema["properties"].get(key, {})
        childprops = prop.get("properties")
        child_item_props = prop.get("items", {}).get("properties")

        if child_item_props:
            for i, _value in enumerate(value):
                # check that child prop has properties
                try:
                    prop["properties"]
                except:
                    message = f"Missing key 'properties' in child prop: {_value}"
                    raise KeyError(message)
                item = flatten_to_json_path(
                    dictionary=_value,
                    schema=prop,
                    parent_key=new_key,
                    sep=f"[{str(i)}]{sep}",
                )
                items.extend(item.items())
        elif childprops:
            item = flatten_to_json_path(
                dictionary=value, schema=prop, parent_key=new_key, sep=sep
            )
            items.extend(item.items())

        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_from_json_path(field):
    """
    Converts a flattened dictionary with key names conforming to
    JSONpath notation to the nested dictionary format.
    """
    field_json = {}

    for prop_path, prop in field.items():
        prop_json = field_json

        nested_names = prop_path.split(".")
        nested_names_length = len(nested_names)
        for i, prop_name in enumerate(nested_names):
            if "[" in prop_name:
                g = re.match(r"(.+)\[(\d+)\]$", prop_name)
                if not g:
                    raise jsonschema.ValidationError(
                        f"Incorrect array indexing in name {prop_name}"
                    )
                try:
                    array_name = g[1]
                    array_index = int(g[2])
                except Exception as e:
                    raise jsonschema.ValidationError(str(e))
                if array_name not in prop_json:
                    prop_json[array_name] = [{} for _ in range(array_index + 1)]
                elif len(prop_json[array_name]) <= array_index:
                    prop_json[array_name].extend(
                        [
                            {}
                            for _ in range(array_index - len(prop_json[array_name]) + 1)
                        ]
                    )
                if i == nested_names_length - 1:
                    if isinstance(prop_json[array_name][array_index], dict):
                        prop_json[array_name][array_index].update({array_name: prop})
                    else:
                        prop_json[array_name][array_index] = {array_name: prop}
                else:
                    prop_json = prop_json[array_name][array_index]
            else:
                if i == nested_names_length - 1:
                    prop_json[prop_name] = prop
                else:
                    if prop_name not in prop_json:
                        prop_json[prop_name] = {}
                    prop_json = prop_json[prop_name]

    return field_json


# json to csv utils
def join_iter(iterable, sep_list="|"):
    """Joins on iterable"""
    return sep_list.join([str(p) for p in iterable])


def join_dict_items(dictionary: dict, sep_key_val="=", sep_items="|"):
    """Joins a mappable collection (ie dictionary) into a string
    representation with specified separators for the key and value
    in addition to items.

    All items are coerced to the string representation (eg if key or value
    is None, this will be coerced to "None")
    """
    dict_list = []
    for key, val in dictionary.items():
        key_str = str(key)
        val_str = str(val)
        dict_list.append(key_str + sep_key_val + val_str)
    return sep_items.join(dict_list)


# Working with schemas
def flatten_properties(properties, parent_key="", sep=".", item_sep=r"\[\d+\]"):
    """Flatten schema properties"""
    properties_flattened = {}
    for key, item in properties.items():
        # flattened keys
        if parent_key:
            flattened_key = parent_key + "." + key
        else:
            flattened_key = key

        if isinstance(item, MutableMapping):
            props = item.get("properties")
            items = item.get("items", {}).get("properties")
            if props:
                new_props = flatten_properties(props, parent_key=flattened_key)
                properties_flattened.update(new_props)

            elif items:
                new_props = flatten_properties(
                    items, parent_key=flattened_key + item_sep
                )
                properties_flattened.update(new_props)
            else:
                properties_flattened[flattened_key] = item

        else:
            properties_flattened[flattened_key] = item

    return properties_flattened


def find_prop_name(column_name, properties):
    """
    Given a dictionary of json schema object properties OR a list of property names, return the
    matching property name.

    This function is needed when a schema is flattened according to a json path
    and converted into a regular expression for list (array) indices.

    """
    prop_match = []
    for name in list(properties):
        if re.match("^" + name + "$", column_name):
            prop_match.append(name)

    if len(prop_match) == 1:
        return prop_match[0]
    elif len(prop_match) > 1:
        raise Exception(
            f"Multiple matching properties found for {column_name}. Can only have one match"
        )
    elif len(prop_match) == 0:
        return None
    else:
        raise Exception(f"Unknown error when matching properties against {column_name}")
