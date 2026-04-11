How to use:
```sh
# Install uv first
# Create a venv
# Install ansible
# Optional: install xfreedrp3 or remmina for RDP (required by rdp.py)
# Optional: install pssh and sshpass for ansible ssh password authentication (required by pssh.sh)
. .env.sh
./build.sh
./ansible-playbook.sh install-playbook.yaml
./ansible-playbook.sh maintain-playbook.yaml
firefox http://127.0.0.1:8006/

# After windows has been installed:
./rdp.py --domain "." # to log in with the local user to the windows machine
./ansible-playbook.sh client-playbook.yaml
./rdp.py --domain "AD" # to log in with the AD user to the windows machine
```
