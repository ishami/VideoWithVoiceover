#!/bin/bash
echo "Starting Gunicorn..."
gunicorn app:app --bind 0.0.0.0:5001 --workers 2 --timeout 300 --log-level debug &
echo "App started on port 5001"
