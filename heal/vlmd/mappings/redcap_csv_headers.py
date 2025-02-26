mapping = {
    "Variable / Field Name": "name",
    "Form Name": "form",
    "Section Header": "section",
    "Field Type": "type",
    "Field Label": "label",
    "Choices, Calculations, OR Slider Labels": "choice_calc_lbls",
    "Field Note": "note",
    "Text Validation Type OR Show Slider Number": "text_valid_slider_num",
    "Text Validation Min": "text_valid_min",
    "Text Validation Max": "text_valid_max",
    "Identifier?": "identifier",
    "Branching Logic (Show field only if...)": "skip_logic",
    "Required Field?": "required",
    "Custom Alignment": "align",
    "Question Number (surveys only)": "question_num",
    "Matrix Group Name": "matrix_group",
}

CHOICES_LABEL_INPUT = "Choices, Calculations, OR Slider Labels"
CHOICES_FIELD_NAME = SLIDER_FIELD_NAME = CALC_FIELD_NAME = mapping[CHOICES_LABEL_INPUT]
TEXT_VALID_FIELD_NAME = mapping["Text Validation Type OR Show Slider Number"]

# This document lists 'Field Label' as required but Google AI excludes it
# https://ws.engr.illinois.edu/sitemanager/getfile.asp?id=1365
redcap_required_fields = [
    "Variable / Field Name",
    "Form Name",
    "Field Type",
    "Field Label",
]
