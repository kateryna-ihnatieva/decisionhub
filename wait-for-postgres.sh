#!/bin/sh

set -e

host="$DB_HOST"
port="$DB_PORT"

echo "⏳ Waiting for PostgreSQL at $host:$port..."

until pg_isready -h "$host" -p "$port" > /dev/null 2>&1; do
  sleep 1
done

echo "✅ PostgreSQL is up. Starting the app..."

python app.py