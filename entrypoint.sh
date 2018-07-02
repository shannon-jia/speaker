#!/bin/bash
set -e

if [ "$1" = 'sam-speaker' ]; then
    exec /app/sam-speaker
fi

exec "$@"
