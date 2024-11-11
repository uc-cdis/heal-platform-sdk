# heal-platform-sdk
<img src="docs/images/gen3-blue-dark.png" width=250px>

The HEAL Platform Software Development Kit (SDK) for Python provides classes and functions for handling HEAL specific tasks.

### qdr_downloads

The qdr_downloads module include a retriever function for downloading files from Syracuse QDR.

This is intended to be called by gen3sdk [external download functions](https://github.com/uc-cdis/gen3sdk-python/blob/master/gen3/tools/download/external_file_download.py). It is also possible to write a wrapper script for the qdr download functions.

### Notebooks

In the notebooks directory there are jupyter notebooks that may be used to download files from a corresponding platform. For instance the qdr_data_download.ipynb notebook may be used to download files from Syracuse QDR.

These notebooks perform optimally within a HEAL Gen3 Workspace and the notebooks will be automatically installed to a user's workspace when the workspace is initiated. However, you may also use these notebooks on your local machine.

### VLMD extraction and validation

The [VLMD documentation](heal/vlmd/README.md) describe how to use the SDK for extracting and validating VLMD dictionaries.

### Run tests

```
poetry run pytest -vv tests
```

### Pip install for using heal-platform-sdk

Until the `heal-platform-sdk` is available on PyPI, any local pip installs should directly
reference the git repo.

As an example, `pip install` can be called from the command line for getting
the master branch of the `heal-platform-sdk`,

```
pip install -e git+https://github.com/uc-cdis/heal-platform-sdk.git#egg=heal
```

or a particular branch, eg,

```
pip install -e git+https://github.com/uc-cdis/heal-platform-sdk.git@my-branch#egg=heal
```

The specification can also be listed in requirements.txt file
(with, say, a tag specification of 0.1.0)

```
pip install -e git+https://github.com/uc-cdis/heal-platform-sdk.git@0.1.0#egg=heal
```

### CLI

The SDK exposes a Command Line Interface (CLI) for some functions.

The CLI can be invoked as follows

`heal [OPTIONS] COMMAND [ARGS]`

For a list of commands and options run

`heal --help`

For example, the following can validate a VLMD file in csv format:

`heal vlmd validate --input_file "vlmd_for_validation.csv"`

The [VLMD documentation](heal/VLMD/README.md)  provides information on
using the VLMD functions, such as `extract` and `validate`.
