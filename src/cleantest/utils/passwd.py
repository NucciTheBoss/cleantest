#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Object-oriented user and group management for test environment instances."""

import grp
import os
import pwd
import shutil
import subprocess
from typing import List, Optional, Union


class UserError(Exception):
    """Raise if error is encountered when performing an operation with users."""


class GroupError(Exception):
    """Raise if error is encountered when performing an operation with groups."""


class User:
    """Manage user on test environment instance.

    Args:
        user (Union[str, User]): User to manage on instance.
    """

    def __init__(self, user: Union[str, "User"]) -> None:
        if type(user) != str and type(user) != type(self):
            raise TypeError(
                f"Argument `user` should be type str or User, not {type(user)}."
            )
        for executable in ["useradd", "userdel"]:
            if shutil.which(executable) is None:
                raise UserError(
                    f"Executable `{executable}` not found on PATH {os.getenv('PATH')}"
                )

        self._user = str(user)

    @property
    def name(self) -> str:
        """Get name of user."""
        return self._user

    @property
    def uid(self) -> Optional[int]:
        """Get uid of user."""
        if self.exists():
            return pwd.getpwnam(self._user).pw_uid
        return None

    @property
    def info(self) -> Optional[pwd.struct_passwd]:
        """Get password database entry struct for user."""
        try:
            return pwd.getpwnam(self._user)
        except KeyError:
            return None

    def exists(self) -> bool:
        """Check if user exists on test environment instance."""
        try:
            pwd.getpwnam(self._user)
            return True
        except KeyError:
            return False

    def add(
        self,
        password: Optional[str] = None,
        shell: Union[str, os.PathLike] = "/bin/bash",
        system_user: bool = False,
        primary_group: Optional[Union[str, "Group"]] = None,
        secondary_groups: Optional[List[Union[str, "Group"]]] = None,
        uid: Optional[int] = None,
        home: Optional[Union[str, os.PathLike]] = None,
    ) -> None:
        """Add user to test environment instance.

        Args:
            password (Optional[str]):
                Encrypted password of the new account. (Default: None).
            shell (Union[str, os.PathLike]):
                The name of the user's login shell. (Default: "/bin/bash").
            system_user (bool):
                Create a system account. (Default: False).
            primary_group (Optional[Union[str, Group]]):
                Name or ID of the primary group of the new account. (Default: None).
            secondary_groups (Optional[List[Union[str. Group]]]):
                List of supplementary groups of the new account. (Default: None).
            uid (Optional[int]):
                User ID of the new account. (Default: None).
            home (Optional[Union[str, os.PathLike]]):
                Home directory of the new account. (Default: None)
        """
        if self.exists():
            raise UserError(f"User {self._user} already exists.")

        cmd = ["useradd", "--shell", str(shell)]
        if password:
            cmd.extend(["--password", password, "--create-home"])
        if system_user or password is None:
            cmd.append("--system")
        if uid:
            cmd.extend(["--uid", uid])
        if home:
            cmd.extend(["--home", str(home)])
        if not primary_group:
            try:
                grp.getgrnam(self._user)
                primary_group = self._user  # Avoid issue where group already exists.
            except KeyError:
                ...
        if primary_group:
            cmd.extend(["--gid", str(primary_group)])
        if secondary_groups:
            cmd.extend(["--groups", ",".join([str(g) for g in secondary_groups])])
        cmd.append(self._user)
        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise UserError(f"{e} Reason:\n{e.stderr}")

    def remove(self, purge: bool = False) -> None:
        """Remove user from test environment instance.

        Args:
            purge (bool): Remove all files, SELinux mappings, home, and mail for user.
        """
        if not self.exists():
            raise UserError(f"User {self._user} does not exist.")

        cmd = ["userdel"]
        if purge:
            cmd.extend(["--force", "--selinux-user", "--remove"])
        cmd.append(self._user)
        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise UserError(f"{e} Reason:\n{e.stderr}")

    def __str__(self) -> str:
        """Get User object as a string."""
        return self._user

    def __repr__(self) -> str:
        """String representation of User class."""
        return f"{self.__class__.__name__}(user: {self._user})"


class Group:
    """Manage group on test environment instance.

    Args:
        group (Union[str, Group]): Group to manage on instance.
    """

    def __init__(self, group: Union[str, "Group"]) -> None:
        if type(group) != str and type(group) != type(self):
            raise TypeError(
                f"Argument `group` should be type str or Group, not {type(group)}."
            )
        for executable in ["addgroup", "groupdel", "gpasswd", "groupmems"]:
            if shutil.which(executable) is None:
                raise GroupError(
                    f"Executable `{executable}` not found on PATH {os.getenv('PATH')}"
                )

        self._group = group

    @property
    def name(self) -> str:
        """Get name of group."""
        return self._group

    @property
    def gid(self) -> Optional[int]:
        """Get gid of group."""
        if self.exists():
            return grp.getgrnam(self._group).gr_gid
        return None

    @property
    def members(self) -> List[str]:
        """Get members of the group."""
        if self.exists():
            return (
                subprocess.run(
                    ["groupmems", "-g", self._group, "-l"],
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                )
                .stdout.strip("\n")
                .split()
            )

        return []

    @property
    def info(self) -> Optional[grp.struct_group]:
        """Get password database entry struct for user."""
        try:
            return grp.getgrnam(self._group)
        except KeyError:
            return None

    def exists(self) -> bool:
        """Check if group exists on test environment instance."""
        try:
            grp.getgrnam(self._group)
            return True
        except KeyError:
            return False

    def add(self, system_group: bool = False, gid: Optional[int] = None) -> None:
        """Add group to test environment instance.

        Args:
            system_group (bool): Add a system group. (Default: False).
            gid (Optional[int]): gid to assign to group. (Default: None).
        """
        if self.exists():
            raise GroupError(f"Group {self._group} already exists.")

        cmd = ["addgroup"]
        if gid:
            cmd.extend(["--gid", gid])
        if system_group:
            cmd.append("--system")
        else:
            cmd.append("--group")
        cmd.append(self._group)
        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise GroupError(f"{e} Reason:\n{e.stderr}")

    def remove(self, force: bool = False) -> None:
        """Remove group from test environment instance.

        Args:
            force (bool): Delete group even if it is the primary group of a user
        """
        if not self.exists():
            raise GroupError(f"Group {self._group} does not exist.")

        cmd = ["groupdel"]
        if force:
            cmd.append("-f")
        cmd.append(self._group)
        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise GroupError(f"{e} Reason:\n{e.stderr}")

    def add_user(self, user: Union[str, User]) -> None:
        """Add user to group on test environment instance.

        Args:
            user (Union[str, User]): User to add to group.
        """
        if not User(user).exists():
            raise UserError(f"User {str(user)} does not exist.")
        if not self.exists():
            raise GroupError(f"Group {self._group} does not exist.")

        try:
            subprocess.check_output(
                ["gpasswd", "--add", str(user), self._group],
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise GroupError(f"{e} Reason:\n{e.stderr}")

    def remove_user(self, user: Union[str, User]) -> None:
        """Remove user from test environment instance.

        Args:
            user (Union[str, User]): User to remove from group.
        """
        if not User(user).exists():
            raise UserError(f"User {str(user)} does not exist.")
        if not self.exists():
            raise GroupError(f"Group {self._group} does not exist.")
        if str(user) not in self.members:
            raise GroupError(f"User {str(user)} is not a member of {self._group}.")

        try:
            subprocess.check_output(
                ["gpasswd", "--delete", str(user), self._group],
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise GroupError(f"{e} Reason:\n{e.stderr}")

    def __str__(self) -> str:
        """Get Group object as a string."""
        return self._group

    def __repr__(self) -> str:
        """String representation of Group class."""
        return f"{self.__class__.__name__}(group: {self._group})"
