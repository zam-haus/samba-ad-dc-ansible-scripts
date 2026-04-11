#!/usr/bin/env bash
set -euxo pipefail
. ./.env.sh
docker compose up -d
sshpass -p "$DOCKER_CONTAINER_SSH_PASSWORD" parallel-ssh -H ansible@localhost:2201 -H ansible@localhost:2202 -A -i -O StrictHostKeyChecking=accept-new "$*"
