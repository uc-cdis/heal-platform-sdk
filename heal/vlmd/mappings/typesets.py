from functools import partial

import pandas as pd
import pandas.api.types as pdt
import visions as v

# for declarative API example used as reference see:
# https://github.com/dylan-profiler/visions/blob/develop/examples/declarative_typeset.py


# for Categorical vision type reference, see ydata-profiling:
# https://github.com/ydataai/ydata-profiling/blob/develop/src/ydata_profiling/model/typeset.py
# state param needed for visions graph traversal
class contains:
    def is_category(series, state):
        return isinstance(series.dtype, pd.CategoricalDtype)
        # return pdt.is_categorical_dtype(series)

    def is_boolean(series, state):
        return pdt.is_bool_dtype(series)


class _transformers:
    def to_category(series, state):
        return pd.Categorical(series)


class _relationships:
    def type_is_category(series, k, threshold):
        nunique = series.nunique()
        few_enough_cats = nunique <= k
        low_enough_thresh = (nunique / series.size) < threshold
        is_not_boolean = not contains.is_boolean(series, None)
        return few_enough_cats and low_enough_thresh and is_not_boolean


class inference_relations:
    def type_to_category(
        related_types=[v.Integer, v.Float, v.String], k=5, threshold=0.2
    ):
        relationships = []
        for vision_type in related_types:
            relation = dict(
                related_type=vision_type,
                relationship=lambda series, state: partial(
                    _relationships.type_is_category, k=k, threshold=threshold
                )(series),
                transformer=_transformers.to_category,
            )
            relationships.append(relation)
        return relationships


# types in the CompleteSet but not in StandardSet
## just manually add additions so additional dependencies
## for unused types not necessary

# {Count,
#  Date,
#  EmailAddress,
#  File,
#  Geometry,
#  IPAddress,
#  Image,
#  Ordinal,
#  Path,
#  Time,
#  URL,
#  UUID}

# TODO: make function to allow specification of params (eg k and threshold). Currently using sensiable default (see typesets_relations.py)
# TODO: should we call this something more "frictionless-y" like "Enum"?
Categorical = v.create_type(
    "Categorical",
    identity=[v.Generic],
    contains=contains.is_category,
    inference=inference_relations.type_to_category(),
)

typeset_original = v.StandardSet() - v.Categorical + v.Date + v.Time
typeset_with_categorical = typeset_original + Categorical

typeset_mapping = {
    "Integer": "integer",
    "Float": "number",
    "String": "string",
    "Time": "time",
    "TimeDelta": "duration",
    "DateTime": "datetime",
    "Boolean": "boolean",
}


def infer_frictionless_fields(
    df,
    typesets=[typeset_original, typeset_with_categorical],
    typeset_mapping=typeset_mapping,
):
    """
    Takes in a dataframe
    and infers types by iterating through typesets.


    NOTE: This multiple typeset iteration was a solution to
    correctly inferring types within categoricals
    (eg, integer categoricals from a float column.
    best solution may be to look into ordering inferences but
    this does the same job.)
    """

    # TODO: infer formats with extended dtypes (eg url, email etc)
    for typeset in typesets:
        df, typepaths, _ = typeset.infer(
            df
        )  # typepaths is list of the visions graph traversal - last item is casted type
    fields = []

    for col, typepath in typepaths.items():
        field = {"name": col}
        if len(typepath) == 1:
            continue
        type_final = str(typepath[-1])
        if type_final == "Categorical":
            # TODO: see visions PR https://github.com/dylan-profiler/visions/issues/160 -- best way
            # would probably be to use networkx graph. seems like this may be a good feature to add
            # to visions package
            type_second_to_final = str(typepath[-2])
            field["type"] = typeset_mapping.get(type_second_to_final, "any")
            # enums for inferred categoricals
            field["constraints"] = {"enum": list(df[col].cat.categories)}
        else:
            field["type"] = typeset_mapping.get(str(type_final), "any")

        if field["type"] == "any":
            print(field["name"])
        fields.append(field)

    return fields
