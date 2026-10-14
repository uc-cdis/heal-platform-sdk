# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Poetry-managed, Python ^3.13. The PyPI package is `heal-sdk`; the import name is `heal`.

```bash
poetry install                                   # install with dev deps
poetry run pytest tests                          # all tests (-vv is already in addopts)
poetry run pytest tests/test_vlmd_extract.py     # one file
poetry run pytest tests/test_vlmd_extract.py::test_name   # one test
poetry run pytest --cov=heal --cov-report xml tests       # what CI runs (tests/ci_commands_script.sh)
poetry run heal vlmd validate --input_file f.csv          # CLI (entry point heal.cli.heal_cli:main)
poetry run heal vlmd extract --input_file f.csv --title "T" --output_dir ./out
```

Formatting is `black` (enforced on PRs by the uc-cdis "Wool" action). Pre-commit also runs `detect-secrets` against `.secrets.baseline` — if a test fixture trips it, update the baseline or add `# pragma: allowlist secret`. Releases publish to PyPI on git tag push; bump `version` in `pyproject.toml`.

## Architecture

Two unrelated halves share the package:

### External file retrievers (`heal/*_downloads.py`)

`qdr_downloads` (Syracuse QDR), `harvard_downloads` (Harvard Dataverse), `mpd_downloads` (Mouse Phenome DB). Each exposes a `get_*_files(wts_hostname, auth, file_metadata_list, download_path)` function returning `Dict[id, DownloadStatus]`. This signature is a contract: they are invoked by Gen3SDK's [external file download](https://github.com/uc-cdis/gen3sdk-python/blob/master/gen3/tools/download/external_file_download.py) machinery, so don't change it. Shared helpers (ID/filename extraction from metadata, WTS IdP token fetch, download + unzip) live in `heal/utils.py`. Tests mock HTTP with `requests-mock`. The `notebooks/` wrap these for use inside HEAL Gen3 Workspaces.

### VLMD (variable-level metadata / data dictionaries, `heal/vlmd/`)

Public API is `vlmd_validate`, `vlmd_extract`, `ExtractionError` from `heal.vlmd` (import order in `heal/vlmd/__init__.py` matters — `extract` imports from `validate`). The CLI in `heal/cli/` is a thin click wrapper over these.

- **Validate converts; extract validates.** `vlmd_validate` on csv/tsv input first converts to VLMD via `convert_to_vlmd`, then validates the converted output against the JSON Schema. `vlmd_extract` for csv/tsv/redcap calls `vlmd_validate(..., return_converted_output=True)` to get its converted dict, then writes it. For json input the flows are reversed (convert, then validate).
- **`file_type="auto"` fallback:** in `vlmd_extract`, if a csv/tsv fails as a data *dictionary*, it retries as a *dataset* (`dataset_csv`/`dataset_tsv`, i.e. infer a dictionary from raw data via `visions` typesets). REDCap exports are auto-detected from headers and raise `RedcapExtractionError`, which skips the dataset fallback.
- **Dispatch chain:** user `file_type` → `file_type_to_fxn_map` (`validate/validate.py`) → input_type string → `choice_fxn` (`extract/conversion.py`) → one of the `extract/*_conversion.py` converters. Converters return `{"template_json": ..., "template_csv": {"fields": [...]}}`.
- **Schemas** `heal/vlmd/schemas/heal_{csv,json}.json` are loaded once at import in `config.py`; `JSON_SCHEMA_VERSION` comes from the json schema's `version`. CSV validation runs against the csv schema after `add_types_to_props` fills in types the csv schema leaves unspecified.
- **`mappings/`** holds field rename/recode maps (csv column names ↔ json paths, value recoding) and REDCap field-type mappings; change these rather than special-casing in converters.
- `heal/vlmd/README.md` lists the steps for adding a new input file type.

Test data lives in `tests/test_data/vlmd/{valid,invalid}/`; shared fixtures (schemas, allowed types) are in `tests/conftest.py`.
