#!/bin/bash
echo "Stopping Gunicorn processes..."
pkill -f "gunicorn app:app"
echo "Gunicorn processes killed (pkill)."
echo "App is now stopped."
