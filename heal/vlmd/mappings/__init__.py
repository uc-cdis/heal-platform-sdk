"""

This module contains all property name and value mappings
for both the json and csv template. Note, the json property names
are represented as json paths. In v0.2 schema versions,csv field property
names must now conform to json path but in prior versions this was not the case.

"""

from .names import rename_map
from .values import recode_map
