## Testing locally in docker
How to use:
```sh
# Install uv first
# Install ansible, e.g. by `uv sync`
# Optional: install xfreedrp3 or remmina for RDP (required by rdp.py)
# Optional: install pssh and sshpass for ansible ssh password authentication (required by pssh.sh)
. .env.sh
./build.sh
./ansible-playbook.sh install-playbook.yaml -e administrator_password='P@ssw0rd'
./ansible-playbook.sh maintain-playbook.yaml -e administrator_password='P@ssw0rd'
firefox http://127.0.0.1:8006/

# After windows has been installed:
./rdp.py --domain "." # to log in with the local user to the windows machine
./ansible-playbook.sh client-playbook.yaml
./rdp.py --domain "AD" # to log in with the AD user to the windows machine
```

## Production

Don't start the docker in production, the windows container has a hardcoded admin password in docker-compose.yml.

Be careful, install-playbook.yaml may reinstall your domain. See the force-reinstall flag.

```shell
 ADMINISTRATOR_PASSWORD=Pa55w0rd ./prod-install.sh
```