#!/usr/bin/env bash
# Render runs this to start the server (Start Command: bash start.sh).
#
# One worker process means one no-show scheduler. Render's default gunicorn
# options are cleared because --preload would keep the scheduler thread out of
# the worker process.
unset GUNICORN_CMD_ARGS

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 \
  --threads 4 \
  --timeout 60
