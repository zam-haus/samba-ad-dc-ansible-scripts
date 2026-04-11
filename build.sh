#!/usr/bin/env bash
set -euxo pipefail
. ./.env.sh
docker compose down
docker compose build
docker compose up -d
ssh-keygen -f "$HOME/.ssh/known_hosts" -R '[localhost]:2201'
ssh-keygen -f "$HOME/.ssh/known_hosts" -R '[localhost]:2202'
docker inspect -f \
  "ssh-keygen -f /home/phi1010/.ssh/known_hosts -R {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" \
  $(docker ps -aq) \
  | grep -P '\d+\.\d+\.\d+\.\d+' \
  | bash
./pssh.sh ""