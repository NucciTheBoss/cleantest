#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Provision LDAP server nodes."""

import pathlib
import tempfile
import textwrap

from cleantest.utils import apt, systemd, run

# Define resources needed to set up LDAP.
slapd_preseed = textwrap.dedent(
    """
    slapd slapd/no_configuration boolean false
    slapd slapd/domain string mini-hpc.org
    slapd shared/organization string mini-hpc
    slapd slapd/password1 password test
    slapd slapd/password2 password test
    slapd slapd/purge_database boolean true
    slapd slapd/move_old_database boolean true
    """
).strip("\n")
default_ldif = textwrap.dedent(
    """
    dn: ou=People,dc=mini-hpc,dc=org
    objectClass: organizationalUnit
    ou: People
    
    dn: ou=Groups,dc=mini-hpc,dc=org
    objectClass: organizationalUnit
    ou: Groups
    
    dn: uid=nucci,ou=People,dc=mini-hpc,dc=org
    uid: nucci
    objectClass: inetOrgPerson
    objectClass: posixAccount
    cn: nucci
    sn: nucci
    givenName: nucci
    mail: nucci@example.com
    userPassword: test
    uidNumber: 10000
    gidNumber: 10000
    loginShell: /bin/bash
    homeDirectory: /home/nucci
    
    dn: cn=nucci,ou=Groups,dc=mini-hpc,dc=org
    cn: nucci
    objectClass: posixGroup
    gidNumber: 10000
    memberUid: nucci
    
    dn: cn=research,ou=Groups,dc=mini-hpc,dc=org
    cn: research
    objectClass: posixGroup
    gidNumber: 10100
    memberUid: nucci
    """
).strip("\n")

# Set up slapd service.
apt.update()
apt.install("slapd", "ldap-utils", "debconf-utils")
with tempfile.NamedTemporaryFile() as preseed, tempfile.NamedTemporaryFile() as ldif:
    pathlib.Path(preseed.name).write_text(slapd_preseed)
    pathlib.Path(ldif.name).write_text(default_ldif)
    results = run(
        f"debconf-set-selections < {preseed.name}",
        "dpkg-reconfigure -f noninteractive slapd",
        (
            "ldapadd -x -D cn=admin,dc=mini-hpc,dc=org -w "
            f"test -f {ldif.name} -H ldap:///"
        ),
    )
    for result in results:
        assert result.exit_code == 0

systemd.restart("slapd")
