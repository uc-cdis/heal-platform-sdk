# heal-platform-sdk
<img src="docs/images/gen3-blue-dark.png" width=250px>

The HEAL Platform Software Development Kit (SDK) for Python provides classes and functions for handling HEAL specific tasks.

### qdr_downloads

The qdr_downloads module include a retriever function for downloading files from Syracuse QDR.

This is intended to be called by gen3sdk [external download functions](https://github.com/uc-cdis/gen3sdk-python/blob/master/gen3/tools/download/external_file_download.py). It is also possible to write a wrapper script for the qdr download functions.

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
pip install -e git+ssh://git@github.com/uc-cdis/heal-platform-sdk.git#egg=heal
```

or a particular branch, eg,

```
pip install -e git+ssh://git@github.com/uc-cdis/heal-platform-sdk.git@feat/add-syracuse-qdr-retriever#egg=heal
```

The specification can also be listed in requirements.txt file
(with, say, a tag specification of 0.1.0)

```
-e git+ssh://git@github.com/uc-cdis/heal-platform-sdk.git@0.1.0#egg=heal
```
