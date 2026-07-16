#!/bin/bash
# Start JavisPi (activates the venv for you)
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
