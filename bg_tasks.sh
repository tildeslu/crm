#!/bin/sh

VENV=${VENV:-/home/slu/.virtualenvs/crm}

PRODUCTION=
[ -z "$DEBUG" ] && PRODUCTION=True
export PRODUCTION

cd `dirname $0`
. $VENV/bin/activate
exec ./manage.py process_tasks
