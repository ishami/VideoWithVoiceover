#!/usr/bin/env python3
from app import app

print("Available routes:")
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods)
    print(f"{rule.rule} [{methods}]")
