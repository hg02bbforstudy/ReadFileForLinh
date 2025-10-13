#!/bin/bash
echo "Starting minimal Flask app..."
echo "PORT: ${PORT:-5000}"
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}