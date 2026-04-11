#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "docopt",
#     "icecream",
# ]
# ///
"""
Usage:
    manage_computer_add.py COMPUTERNAME [--output-windows-script] [--remove-before]

Options:
    -h --help     Show this help message.
    -w --output-windows-script   Output a Windows script to join the domain.
    -f --force --remove-before   Remove the computer before adding it (if it exists).
"""
import subprocess
import os
import sys
from docopt import docopt
from secrets import choice
from string import ascii_letters, digits
import shlex
from icecream import ic
import logging

log = logging.getLogger(__name__)


# Password generator (12 chars, letters and digits)
def generate_password(length=12):
    alphabet = ascii_letters + digits
    return ''.join(choice(alphabet) for _ in range(length))


def test_generate_password():
    pwd = generate_password(length=1000)
    assert len(pwd) == 1000
    assert any(c.islower() for c in pwd)
    assert any(c.isupper() for c in pwd)
    assert any(c.isdigit() for c in pwd)


def main(args):
    PASS = os.getenv("PASS")
    if not PASS:
        log.fatal("Error: PASS environment variable not set.")
        sys.exit(1)

    computer_name = args["COMPUTERNAME"]
    computer_password = generate_password()
    output_windows_script = args["--output-windows-script"]
    remove_before = args["--remove-before"]

    ssh_base = ["sshpass", "-p", PASS, "ssh", "ansible@localhost", "-p", "2201"]

    add_computer(computer_name, computer_password, ssh_base)

    if output_windows_script:
        assert not any(
            c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`'
            for c in computer_password), "Password contains special characters, cannot generate script."
        log.info("Execute the following script to join the windows computer to the domain:")
        print('''
$joinCred = New-Object pscredential -ArgumentList ([pscustomobject]@{
    UserName = $null
    Password = (ConvertTo-SecureString -String "''' + computer_password + '''" -AsPlainText -Force)[0]
})
$addComputerSplat = @{
    DomainName = "ad.zam.haus"
    Options = 'UnsecuredJoin', 'PasswordPass'
    Credential = $joinCred
}
Add-Computer @addComputerSplat
        ''')


def add_computer(computer_name, computer_password: str, ssh_base: list[str]):
    # Add computer
    add_cmd = ssh_base + [shlex.join(["sudo", "samba-tool", "computer", "add", computer_name])]
    result = subprocess.run(
        add_cmd,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        log.fatal(f"Error adding computer.")
        sys.exit(result.returncode)

    # Set computer password
    setpw_cmd = ssh_base + [f"sudo samba-tool user setpassword '{computer_name}$' --newpassword='{computer_password}'"]
    result = subprocess.run(
        setpw_cmd,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        log.fatal(f"Error setting password.")
        sys.exit(result.returncode)

    log.info(f"Added computer '{computer_name}' with password '{computer_password}'")


if __name__ == "__main__":
    ic.configureOutput(outputFunction=log.debug)
    logging.basicConfig(level=logging.DEBUG)
    arguments = docopt(__doc__)
    ic(arguments)
    main(arguments)
