#!/bin/bash
set -euxo pipefail
. ./.env.sh
ANSIBLE_STDOUT_CALLBACK=debug \
  uv run ansible-playbook \
  -i inventory-prod.py \
  -e administrator_password="$ADMINISTRATOR_PASSWORD" \
  maintain-playbook.yaml
