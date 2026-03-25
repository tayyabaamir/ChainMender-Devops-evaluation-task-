#!/bin/bash
set -e
cd /app
python -m pytest /app/tests/test_outputs.py -v --tb=short
