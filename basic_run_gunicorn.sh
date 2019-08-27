#!/bin/bash
# basic_run_gunicorn.sh: Runs gunicorn using the app from basic_run.py.

# The syntax is basically the same as in basic_run.py.
# I use 4 threads and some custom logging.
# See the Gunicorn docs for more information on how this works.
gunicorn --bind=0.0.0.0:443 --certfile cert.pem --keyfile key.pem --access-logfile access.log --access-logformat "%(h)s %(r)s %({Host}i)s %(U)s%(q)s %(s)s %(a)s" --threads 4 basic_run:wm
