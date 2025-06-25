#!/bin/bash
export PYTHONPATH=$PWD
poetry run pytest --cov=app tests 