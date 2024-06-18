#!/usr/bin/env bash

# run tests
poetry run pytest -vv --cov=heal --cov-report xml tests