#!/bin/bash
# start.sh - Simple start script for Railway

# Get PORT from environment or default to 5000
PORT=${PORT:-5000}

echo "Starting Flask app on port $PORT"

# Start gunicorn
exec gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info