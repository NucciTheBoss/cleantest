#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Provision NFS server nodes."""

import pathlib
import textwrap

from cleantest.utils import apt, systemd, run

# Define resources needed to set up nfs-kernel-server.
default_exports = textwrap.dedent(
    """
    /srv     *(ro,sync,subtree_check)
    /home    *(rw,sync,no_subtree_check)
    /data    *(rw,sync,no_subtree_check,no_root_squash)
    /opt     *(rw,sync,no_subtree_check,no_root_squash)
    """
).strip("\n")

# Set up SSSD service.
apt.update()
apt.install("nfs-kernel-server", "sssd-ldap")
for result in run(
    "mv /root/.init/sssd.conf /etc/sssd/sssd.conf",
    "chmod 0600 /etc/sssd/sssd.conf",
    "pam-auth-update --enable mkhomedir",
):
    assert result.exit_code == 0

systemd.restart("sssd")

# Set up NFS kernel server.
for result in run(
    "mkdir -p /data/nucci",
    "mkdir -p /home/nucci",
    "chown -R nucci:nucci /data/nucci",
    "chown -R nucci:nucci /home/nucci",
    "chmod 0755 /data",
    "chmod -R 0750 /data/nucci",
    "chmod -R 0740 /home/nucci",
    "ln -s /data/nucci /home/nucci/data",
):
    assert result.exit_code == 0

pathlib.Path("/etc/exports").write_text(default_exports)
for result in run("exportfs -a"):
    assert result.exit_code == 0

systemd.restart("nfs-kernel-server")
