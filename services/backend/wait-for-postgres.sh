#!/bin/bash
set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD="dev_password" psql -h "$host" -U "commute_planner" -d "commute_planner" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd