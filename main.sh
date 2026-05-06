#!/bin/bash
uv run src/main.py
cd docs && python3 -m http.server 8888
