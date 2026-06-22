#!/usr/bin/env sh
# Builds and starts every container (Postgres + 3 backends + frontend).
# Usage:  ./start.sh          start everything (build if needed)
#         ./start.sh down     stop and remove everything
#         ./start.sh logs     follow logs after starting
set -e

cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
    echo "Docker engine is not running. Start Docker and try again." >&2
    exit 1
fi

if [ "$1" = "down" ]; then
    echo "Stopping and removing all containers..."
    docker compose down
    exit 0
fi

echo "Building and starting all services..."
docker compose up --build -d

echo
docker compose ps
echo
echo "Services are up:"
echo "  Frontend   ->  http://localhost:13000"
echo "  Customer   ->  http://localhost:18001/docs"
echo "  Worker     ->  http://localhost:18002/docs"
echo "  Partner    ->  http://localhost:18003/docs"
echo "  Postgres   ->  localhost:55432  (user/password/mydb)"
echo
echo "Stop everything with:  ./start.sh down"

if [ "$1" = "logs" ]; then
    docker compose logs -f
fi
