#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Provision slurmd nodes."""

import json
import pathlib
from io import StringIO

from cleantest.utils import apt, systemd, run

# Set up SSSD service.
apt.update()
apt.install("slurmd", "nfs-common", "sssd-ldap")
for result in run(
    "mv /root/.init/sssd.conf /etc/sssd/sssd.conf",
    "chmod 0600 /etc/sssd/sssd.conf",
    "pam-auth-update --enable mkhomedir",
):
    assert result.exit_code == 0

systemd.restart("sssd")

# Set up NFS mount.
nfs_ip = json.load(StringIO(pathlib.Path("/root/.init/nfs-0").read_text()))
for result in run(
    f"mount {nfs_ip['nfs-0']}:/home /home",
    "mkdir -p /data",
    f"mount {nfs_ip['nfs-0']}:/data /data",
):
    assert result.exit_code == 0

# Set up munge key.
for result in run(
    "mv /root/.init/munge.key /etc/munge/munge.key",
    "chown munge:munge /etc/munge/munge.key",
    "chmod 0600 /etc/munge/munge.key",
):
    assert result.exit_code == 0

systemd.restart("munge")
