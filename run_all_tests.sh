#!/bin/bash
export PYTHONPATH=$PWD

./run_unit_tests.sh && ./run_e2e_tests.sh