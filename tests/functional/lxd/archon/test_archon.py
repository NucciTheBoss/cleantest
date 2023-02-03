#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Test LXDArchon functionality."""

import json
import os
import pathlib
from io import StringIO

from jinja2 import Environment, FileSystemLoader

from cleantest.control.hooks import StopEnvHook
from cleantest.control.lxd import InstanceConfig
from cleantest.data import File
from cleantest.provider import lxd, LXDArchon

root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
templates = Environment(loader=FileSystemLoader(root / "templates"))


@lxd.target("slurmctld-0")
def run_job():
    import os
    import pathlib
    import shutil
    import textwrap
    from time import sleep

    from cleantest.utils import run

    tmp_dir = pathlib.Path("/tmp")
    (tmp_dir / "research.submit").write_text(
        textwrap.dedent(
            """
            #!/bin/bash
            #SBATCH --job-name=research
            #SBATCH --partition=all
            #SBATCH --nodes=1
            #SBATCH --ntasks-per-node=1
            #SBATCH --cpus-per-task=1
            #SBATCH --mem=500mb
            #SBATCH --time=00:00:30
            #SBATCH --error=research.err
            #SBATCH --output=research.out
            
            echo "I love doing research!"
            """
        ).strip("\n")
    )

    # Set user to test cluster user nucci.
    os.setuid(10000)
    os.chdir("/home/nucci")
    for result in run(
        f"cp {(tmp_dir / 'research.submit')} .",
        "sbatch research.submit",
    ):
        assert result.exit_code == 0
    sleep(60)
    shutil.copy("research.out", (tmp_dir / "result"))


def test_lxd_archon_local() -> None:
    """Test LXDArchon against local LXD cluster."""
    archon = LXDArchon()
    archon.config.register_hook(
        StopEnvHook(name="get_result", download=[File("/tmp/result", root / "result")])
    )
    _ = archon.config.get_instance_config("ubuntu-jammy-amd64").dict()
    _["name"] = "mini-hpc-sm"
    archon.config.add_instance_config(
        InstanceConfig(
            config={
                "limits.cpu": "1",
                "limits.memory": "8GB",
                "security.privileged": "true",
                "raw.apparmor": "mount fstype=nfs*, mount fstype=rpc_pipefs,",
            },
            **_,
        )
    )
    archon.add(
        "ldap-0",
        image="mini-hpc-sm",
        provision_script=root / "ldap_provision_script.py",
    )
    sssd_conf = StringIO(
        templates.get_template("sssd.conf.tmpl").render(
            ldap_server_address=archon.get_public_address("ldap-0")
        )
    )
    archon.add(
        "nfs-0",
        image="mini-hpc-sm",
        provision_script=root / "nfs_provision_script.py",
        resources=[File(sssd_conf, "/root/.init/sssd.conf")],
    )
    nfs_ip = json.dumps({"nfs-0": str(archon.get_public_address("nfs-0"))})
    archon.add(
        "slurmctld-0",
        image="mini-hpc-sm",
        provision_script=root / "slurmctld_provision_script.py",
        resources=[
            File(sssd_conf, "/root/.init/sssd.conf"),
            File(StringIO(nfs_ip), "/root/.init/nfs-0"),
        ],
    )
    archon.pull(
        "slurmctld-0", data_obj=[File("/etc/munge/munge.key", root / "munge.key")]
    )
    archon.add(
        ["slurmd-0", "slurmd-1", "slurmd-2"],
        image="mini-hpc-sm",
        provision_script=root / "slurmd_provision_script.py",
        resources=[
            File(sssd_conf, "/root/.init/sssd.conf"),
            File(StringIO(nfs_ip), "/root/.init/nfs-0"),
            File(root / "munge.key", "/root/.init/munge.key"),
        ],
    )
    slurm_node_info = {
        "slurmctld_name": "slurmctld-0",
        "slurmctld_address": archon.get_public_address("slurmctld-0"),
        "slurmd_0_name": "slurmd-0",
        "slurmd_0_address": archon.get_public_address("slurmd-0"),
        "slurmd_1_name": "slurmd-1",
        "slurmd_1_address": archon.get_public_address("slurmd-1"),
        "slurmd_2_name": "slurmd-2",
        "slurmd_2_address": archon.get_public_address("slurmd-2"),
    }
    slurm_conf = StringIO(
        templates.get_template("slurm.conf.tmpl").render(**slurm_node_info)
    )
    for node in ["slurmctld-0", "slurmd-0", "slurmd-1", "slurmd-2"]:
        archon.push(node, data_obj=[File(slurm_conf, "/etc/slurm/slurm.conf")])
    archon.execute("slurmctld-0", command="systemctl start slurmctld")
    archon.execute(
        ["slurmd-0", "slurmd-1", "slurmd-2"], command="systemctl start slurmd"
    )
    for name, result in run_job():
        assert "I love doing research!" in pathlib.Path(root / "result").read_text()
    (root / "munge.key").unlink(missing_ok=True)
    (root / "result").unlink(missing_ok=True)
    archon.execute(
        ["slurmctld-0", "slurmd-0", "slurmd-1", "slurmd-2"],
        command=f"umount /home /data",
    )
    archon.destroy()
