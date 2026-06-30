#!/bin/sh
set -e

echo "Running database migrations..."
.venv/bin/alembic upgrade head

echo "Starting MailCraft..."
exec .venv/bin/mailcraft
