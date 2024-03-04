#!/usr/bin/env bash

flake8
mypy
coverage run -m pytest
cov-tree -smc -t 95
