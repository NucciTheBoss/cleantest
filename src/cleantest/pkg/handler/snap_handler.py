#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Handler for installing and managing snap packages inside a remote instance."""

import http.client
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
from subprocess import CalledProcessError, CompletedProcess
from typing import Dict, Iterable, List, Optional

from cleantest.pkg._base import PackageError

# Filter for extracting 7-bit C1 ANSI sequences from a string.
ansi_filter = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class SnapAPIError(Exception):
    """Raised when an HTTP API error occurs talking to the Snapd server."""

    def __init__(self, body: Dict, code: int, status: str, message: str):
        """This shouldn't be instantiated directly."""
        super().__init__(message)  # Makes str(e) return message
        self.body = body
        self.code = code
        self.status = status
        self._message = message

    def __repr__(self):
        """String representation of the SnapAPIError class."""
        return f"APIError({self.body}, {self.code}, {self.status}, {self._message})"


class SnapState(Enum):
    """The state of a snap on the system or in the cache."""

    PRESENT = "present"
    ABSENT = "absent"
    LATEST = "latest"
    AVAILABLE = "available"


def _cache_init(func):
    def inner(*args, **kwargs):
        if _Cache.cache is None:
            _Cache.cache = SnapCache()
        return func(*args, **kwargs)

    return inner


class MetaCache(type):
    """MetaCache class used for initialising the snap cache."""

    @property
    def cache(cls) -> "SnapCache":
        """Property for returning the snap cache."""
        return cls._cache

    @cache.setter
    def cache(cls, cache: "SnapCache") -> None:
        """Setter for the snap cache."""
        cls._cache = cache

    def __getitem__(cls, name) -> "Snap":
        """Snap cache getter."""
        return cls._cache[name]


class _Cache(object, metaclass=MetaCache):
    _cache = None


class SnapService:
    """Data wrapper for snap services."""

    def __init__(
        self,
        daemon: Optional[str] = None,
        daemon_scope: Optional[str] = None,
        enabled: bool = False,
        active: bool = False,
        activators: List[str] = [],
        **kwargs,
    ):
        self.daemon = daemon
        self.daemon_scope = kwargs.get("daemon-scope", None) or daemon_scope
        self.enabled = enabled
        self.active = active
        self.activators = activators


class Snap:
    """Represents a snap package and its properties.

    `Snap` exposes the following properties about a snap:
      - name: the name of the snap
      - state: a `SnapState` representation of its install status
      - channel: "stable", "candidate", "beta", and "edge" are common
      - revision: a string representing the snap's revision
      - confinement: "classic" or "strict"
    """

    def __init__(
        self,
        name,
        state: SnapState,
        channel: str,
        revision: str,
        confinement: str,
        apps: Optional[List[Dict[str, str]]] = None,
        cohort: Optional[str] = "",
    ) -> None:
        self._name = name
        self._state = state
        self._channel = channel
        self._revision = revision
        self._confinement = confinement
        self._cohort = cohort
        self._apps = apps or []
        self._snap_client = SnapClient()

    def __eq__(self, other) -> bool:
        """Equality for comparison."""
        return isinstance(other, self.__class__) and (
            self._name,
            self._revision,
        ) == (other._name, other._revision)

    def __hash__(self):
        """A basic hash so this class can be used in Mappings and dicts."""
        return hash((self._name, self._revision))

    def __repr__(self):
        """A representation of the snap."""
        return f"<{self.__module__}.{self.__class__.__name__}: {self.__dict__}>"

    def __str__(self):
        """A human-readable representation of the snap."""
        return f"<{self.__class__.__name__}: {self._name}-{self._revision}.{self._channel} -- {str(self._state)}>"

    def _snap(self, command: str, optargs: Optional[Iterable[str]] = None) -> str:
        """Perform a snap operation.

        Args:
          command: the snap command to execute
          optargs: an (optional) list of additional arguments to pass,
            commonly confinement or channel

        Raises:
          PackageError: If there is a problem encountered.
        """
        optargs = optargs or []
        _cmd = ["snap", command, self._name, *optargs]
        try:
            return subprocess.check_output(_cmd, universal_newlines=True)
        except CalledProcessError as e:
            raise PackageError(
                f"Snap: {self._name}; command {_cmd} failed with output = {e.output}"
            )

    def _snap_daemons(
        self,
        command: List[str],
        services: Optional[List[str]] = None,
    ) -> CompletedProcess:

        if services:
            # an attempt to keep the command constrained to the snap instance's services
            services = [f"{self._name}.{service}" for service in services]
        else:
            services = [self._name]

        _cmd = ["snap", *command, *services]

        try:
            return subprocess.run(_cmd, universal_newlines=True, check=True, capture_output=True)
        except CalledProcessError as e:
            raise PackageError(f"Could not {_cmd} for snap [{self._name}]: {e.stderr}")

    def get(self, key) -> str:
        """Gets a snap configuration value.

        Args:
            key: The key to retrieve
        """
        return self._snap("get", [key]).strip()

    def set(self, config: Dict) -> str:
        """Sets a snap configuration value.

        Args:
           config: A dictionary containing keys and values specifying the config to set.
        """
        args = [f'{key}="{val}"' for key, val in config.items()]

        return self._snap("set", [*args])

    def unset(self, key) -> str:
        """Unsets a snap configuration value.

        Args:
            key: the key to unset.
        """
        return self._snap("unset", [key])

    def start(self, services: Optional[List[str]] = None, enable: Optional[bool] = False) -> None:
        """Starts a snap's services.

        Args:
            services (list): (Optional) List of individual snap services to start (otherwise all).
            enable (bool): (Optional) Flag to enable snap services on start. Default `false`.
        """
        args = ["start", "--enable"] if enable else ["start"]
        self._snap_daemons(args, services)

    def stop(self, services: Optional[List[str]] = None, disable: Optional[bool] = False) -> None:
        """Stops a snap's services.

        Args:
            services (list): (Optional) List of individual snap services to stop (otherwise all).
            disable (bool): (Optional) Flag to disable snap services on stop. Default `False`.
        """
        args = ["stop", "--disable"] if disable else ["stop"]
        self._snap_daemons(args, services)

    def logs(self, services: Optional[List[str]] = None, num_lines: Optional[int] = 10) -> str:
        """Shows a snap services' logs.

        Args:
            services (List[str]): (Optional) List of individual snap services to show logs from
                (otherwise all).
            num_lines (int): (Optional) Integer number of log lines to return. Default `10`.
        """
        args = ["logs", f"-n={num_lines}"] if num_lines else ["logs"]
        return self._snap_daemons(args, services).stdout

    def restart(
        self, services: Optional[List[str]] = None, reload: Optional[bool] = False
    ) -> None:
        """Restarts a snap's services.

        Args:
            services (list): (Optional) List of individual snap services to show logs from
                (otherwise all).
            reload (bool): (Optional) Flag to use the service reload command, if available.
                Default `False`.
        """
        args = ["restart", "--reload"] if reload else ["restart"]
        self._snap_daemons(args, services)

    def _install(self, channel: Optional[str] = "", cohort: Optional[str] = "") -> None:
        """Add a snap to the system.

        Args:
          channel: The channel to install from.
          cohort: Optional, the key of a cohort that this snap belongs to.
        """
        cohort = cohort or self._cohort

        args = []
        if self.confinement == "classic":
            args.append("--classic")
        if channel:
            args.append(f'--channel="{channel}"')
        if cohort:
            args.append(f'--cohort="{cohort}"')

        self._snap("install", args)

    def _refresh(
        self,
        channel: Optional[str] = "",
        cohort: Optional[str] = "",
        leave_cohort: Optional[bool] = False,
    ) -> None:
        """Refresh a snap.

        Args:
          channel: The channel to install from.
          cohort: optionally, specify a cohort.
          leave_cohort: leave the current cohort.
        """
        channel = f'--channel="{channel}"' if channel else ""
        args = [channel]

        if not cohort:
            cohort = self._cohort

        if leave_cohort:
            self._cohort = ""
            args.append("--leave-cohort")
        elif cohort:
            args.append(f'--cohort="{cohort}"')

        self._snap("refresh", args)

    def _remove(self) -> str:
        """Removes a snap from the system."""
        return self._snap("remove")

    @property
    def name(self) -> str:
        """Returns the name of the snap."""
        return self._name

    def ensure(
        self,
        state: SnapState,
        classic: Optional[bool] = False,
        channel: Optional[str] = "",
        cohort: Optional[str] = "",
    ):
        """Ensures that a snap is in a given state.

        Args:
          state: A `SnapState` to reconcile to.
          classic: An (Optional) boolean indicating whether classic confinement should be used.
          channel: The channel to install from.
          cohort: Optional. Specify the key of a snap cohort.

        Raises:
          PackageError: If an error is encountered.
        """
        self._confinement = "classic" if classic or self._confinement == "classic" else ""

        if state not in (SnapState.PRESENT, SnapState.LATEST):
            # We are attempting to remove this snap.
            if self._state in (SnapState.PRESENT, SnapState.LATEST):
                # The snap is installed, so we run _remove.
                self._remove()
            else:
                # The snap is not installed -- no need to do anything.
                pass
        else:
            # We are installing or refreshing a snap.
            if self._state not in (SnapState.PRESENT, SnapState.LATEST):
                # The snap is not installed, so we install it.
                self._install(channel, cohort)
            else:
                # The snap is installed, but we are changing it (e.g., switching channels).
                self._refresh(channel, cohort)

        self._update_snap_apps()
        self._state = state

    def _update_snap_apps(self) -> None:
        """Updates a snap's apps after snap changes state."""
        try:
            self._apps = self._snap_client.get_installed_snap_apps(self._name)
        except SnapAPIError:
            self._apps = []

    @property
    def present(self) -> bool:
        """Returns whether a snap is present."""
        return self._state in (SnapState.PRESENT, SnapState.LATEST)

    @property
    def latest(self) -> bool:
        """Returns whether the snap is the most recent version."""
        return self._state is SnapState.LATEST

    @property
    def state(self) -> SnapState:
        """Returns the current snap state."""
        return self._state

    @state.setter
    def state(self, state: SnapState) -> None:
        """Sets the snap state to a given value.

        Args:
          state: A `SnapState` to reconcile the snap to.

        Raises:
          PackageError: If an error is encountered.
        """
        if self._state is not state:
            self.ensure(state)
        self._state = state

    @property
    def revision(self) -> str:
        """Returns the revision for a snap."""
        return self._revision

    @property
    def channel(self) -> str:
        """Returns the channel for a snap."""
        return self._channel

    @property
    def confinement(self) -> str:
        """Returns the confinement for a snap."""
        return self._confinement

    @property
    def apps(self) -> List:
        """Returns (if any) the installed apps of the snap."""
        self._update_snap_apps()
        return self._apps

    @property
    def services(self) -> Dict:
        """Returns (if any) the installed services of the snap."""
        self._update_snap_apps()
        services = {}
        for app in self._apps:
            if "daemon" in app:
                services[app["name"]] = SnapService(**app).__dict__

        return services


class _UnixSocketConnection(http.client.HTTPConnection):
    """Implementation of HTTPConnection that connects to a named Unix socket."""

    def __init__(self, host, timeout=None, socket_path=None):
        if timeout is None:
            super().__init__(host)
        else:
            super().__init__(host, timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        """Override connect to use Unix socket (instead of TCP socket)."""
        if not hasattr(socket, "AF_UNIX"):
            raise NotImplementedError(f"Unix sockets not supported on {sys.platform}")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)
        if self.timeout is not None:
            self.sock.settimeout(self.timeout)


class _UnixSocketHandler(urllib.request.AbstractHTTPHandler):
    """Implementation of HTTPHandler that uses a named Unix socket."""

    def __init__(self, socket_path: str):
        super().__init__()
        self.socket_path = socket_path

    def http_open(self, req) -> http.client.HTTPResponse:
        """Override http_open to use a Unix socket connection (instead of TCP)."""
        return self.do_open(_UnixSocketConnection, req, socket_path=self.socket_path)


class SnapClient:
    """Snapd API client to talk to HTTP over UNIX sockets.

    In order to avoid shelling out and/or involving sudo in calling the snapd API,
    use a wrapper based on the Pebble Client, trimmed down to only the utility methods
    needed for talking to snapd.
    """

    def __init__(
        self,
        socket_path: str = "/run/snapd.socket",
        opener: Optional[urllib.request.OpenerDirector] = None,
        base_url: str = "http://localhost/v2/",
        timeout: float = 5.0,
    ):
        """Initialize a client instance.

        Args:
            socket_path: a path to the socket on the filesystem. Defaults to /run/snap/snapd.socket
            opener: specifies an opener for unix socket, if unspecified a default is used
            base_url: base url for making requests to the snap client. Defaults to
                http://localhost/v2/
            timeout: timeout in seconds to use when making requests to the API. Default is 5.0s.
        """
        if opener is None:
            opener = self._get_default_opener(socket_path)
        self.opener = opener
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    def _get_default_opener(cls, socket_path):
        """Build the default opener to use for requests (HTTP over Unix socket)."""
        opener = urllib.request.OpenerDirector()
        opener.add_handler(_UnixSocketHandler(socket_path))
        opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
        opener.add_handler(urllib.request.HTTPRedirectHandler())
        opener.add_handler(urllib.request.HTTPErrorProcessor())
        return opener

    def _request(
        self,
        method: str,
        path: str,
        query: Dict = None,
        body: Dict = None,
    ) -> dict | List:
        """Make a JSON request to the Snapd server with the given HTTP method and path.

        If query dict is provided, it is encoded and appended as a query string
        to the URL. If body dict is provided, it is serialized as JSON and used
        as the HTTP body (with Content-Type: "application/json"). The resulting
        body is decoded from JSON.
        """
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        response = self._request_raw(method, path, query, headers, data)
        return json.loads(response.read().decode())["result"]

    def _request_raw(
        self,
        method: str,
        path: str,
        query: Dict = None,
        headers: Dict = None,
        data: bytes = None,
    ) -> http.client.HTTPResponse:
        """Make a request to the Snapd server; return the raw HTTPResponse object."""
        url = self.base_url + path
        if query:
            url = url + "?" + urllib.parse.urlencode(query)

        if headers is None:
            headers = {}
        request = urllib.request.Request(url, method=method, data=data, headers=headers)

        try:
            response = self.opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            code = e.code
            status = e.reason
            message = ""
            try:
                body = json.loads(e.read().decode())["result"]
            except (IOError, ValueError, KeyError) as e2:
                # Will only happen on read error or if Pebble sends invalid JSON.
                body = {}
                message = f"{type(e2).__name__} - {e2}"
            raise SnapAPIError(body, code, status, message)
        except urllib.error.URLError as e:
            raise SnapAPIError({}, 500, "Not found", e.reason)
        return response

    def get_installed_snaps(self) -> Dict:
        """Get information about currently installed snaps."""
        return self._request("GET", "snaps")

    def get_snap_information(self, name: str) -> Dict:
        """Query the snap server for information about single snap."""
        return self._request("GET", "find", {"name": name})[0]

    def get_installed_snap_apps(self, name: str) -> List:
        """Query the snap server for apps belonging to a named, currently installed snap."""
        return self._request("GET", "apps", {"names": name, "select": "service"})


class SnapCache(Mapping):
    """An abstraction to represent installed/available packages.

    When instantiated, `SnapCache` iterates through the list of installed
    snaps using the `snapd` HTTP API, and a list of available snaps by reading
    the filesystem to populate the cache. Information about available snaps is lazily-loaded
    from the `snapd` API when requested.
    """

    def __init__(self):
        if not self.snapd_installed:
            raise PackageError("snapd is not installed or not in /usr/bin") from None
        self._snap_client = SnapClient()
        self._snap_map = {}
        if self.snapd_installed:
            self._load_available_snaps()
            self._load_installed_snaps()

    def __contains__(self, key: str) -> bool:
        """Magic method to ease checking if a given snap is in the cache."""
        return key in self._snap_map

    def __len__(self) -> int:
        """Returns number of items in the snap cache."""
        return len(self._snap_map)

    def __iter__(self) -> Iterable["Snap"]:
        """Magic method to provide an iterator for the snap cache."""
        return iter(self._snap_map.values())

    def __getitem__(self, snap_name: str) -> Snap:
        """Return either the installed version or latest version for a given snap."""
        snap = self._snap_map.get(snap_name, None)
        if snap is None:
            # The snapd cache file may not have existed when _snap_map was
            # populated.  This is normal.
            try:
                self._snap_map[snap_name] = self._load_info(snap_name)
            except SnapAPIError:
                raise PackageError(f"Snap '{snap_name}' not found!")

        return self._snap_map[snap_name]

    @property
    def snapd_installed(self) -> bool:
        """Check whether snapd has been installed on the system."""
        return os.path.isfile("/usr/bin/snap")

    def _load_available_snaps(self) -> None:
        """Load the list of available snaps from disk.

        Leave them empty and lazily load later if asked for.
        """
        if not os.path.isfile("/var/cache/snapd/names"):
            # The snap catalog may not be populated yet; this is normal.
            # snapd updates the cache infrequently and the cache file may not
            # currently exist.
            return

        with open("/var/cache/snapd/names", "r") as f:
            for line in f:
                if line.strip():
                    self._snap_map[line.strip()] = None

    def _load_installed_snaps(self) -> None:
        """Load the installed snaps into the dict."""
        installed = self._snap_client.get_installed_snaps()

        for i in installed:
            snap = Snap(
                name=i["name"],
                state=SnapState.LATEST,
                channel=i["channel"],
                revision=i["revision"],
                confinement=i["confinement"],
                apps=i.get("apps", None),
            )
            self._snap_map[snap.name] = snap

    def _load_info(self, name) -> Snap:
        """Load info for snaps which are not installed if requested.

        Args:
            name: A string representing the name of the snap.
        """
        info = self._snap_client.get_snap_information(name)

        return Snap(
            name=info["name"],
            state=SnapState.AVAILABLE,
            channel=info["channel"],
            revision=info["revision"],
            confinement=info["confinement"],
            apps=None,
        )


@_cache_init
def install(
    snap_names: str | List[str],
    state: str | SnapState = SnapState.LATEST,
    channel: Optional[str] = "latest",
    classic: Optional[bool] = False,
    cohort: Optional[str] = "",
) -> Snap | List[Snap]:
    """Install a snap or snaps in a remote process.

    Args:
        snap_names: The name or names of the snaps to install.
        state: A string or `SnapState` representation of the desired state, one of
            [`PRESENT` or `LATEST`].
        channel: An (Optional) channel as a string. Defaults to 'latest'.
        classic: An (Optional) boolean specifying whether it should be added with classic
            confinement. Default `False`.
        cohort: Optional, the key of a cohort that this snap belongs to.

    Raises:
        PackageError: If some snaps failed to install or were not found.
    """
    snap_names = [snap_names] if type(snap_names) is str else snap_names
    if not snap_names:
        raise TypeError("Expected at least one snap to add, received zero!")

    if type(state) is str:
        state = SnapState(state)

    return _wrap_snap_operations(snap_names, state, channel, classic, cohort)


@_cache_init
def remove(snap_names: str | List[str]) -> Snap | List[Snap]:
    """Removes a snap from the system.

    Args:
        snap_names: The name or names of the snaps to install.

    Raises:
        PackageError: If some snaps failed to install.
    """
    snap_names = [snap_names] if type(snap_names) is str else snap_names
    if not snap_names:
        raise TypeError("Expected at least one snap to add, received zero!")

    return _wrap_snap_operations(snap_names, SnapState.ABSENT, "", False)


@_cache_init
def ensure(
    snap_names: str | List[str],
    state: str,
    channel: Optional[str] = "latest",
    classic: Optional[bool] = False,
    cohort: Optional[str] = "",
) -> Snap | List[Snap]:
    """Ensures a snap is in a given state to the system.

    Args:
        snap_names: The name(s) of the snaps to operate on.
        state: A string representation of the desired state, from `SnapState`.
        channel: An (Optional) channel as a string. Defaults to 'latest'.
        classic: An (Optional) boolean specifying whether it should be added with classic.
            confinement. Default `False`
        cohort: Optional, the key of a cohort that this snap belongs to.

    Raises:
        PackageError: If the snap is not in the cache.
    """
    if state in ("present", "latest"):
        return install(snap_names, SnapState(state), channel, classic, cohort)
    else:
        return remove(snap_names)


def _wrap_snap_operations(
    snap_names: List[str],
    state: SnapState,
    channel: str,
    classic: bool,
    cohort: Optional[str] = "",
) -> Snap | List[Snap]:
    """Wrap common operations for bare commands."""
    snaps = {"success": [], "failed": []}

    for s in snap_names:
        try:
            snap = _Cache[s]
            if state is SnapState.ABSENT:
                snap.ensure(state=SnapState.ABSENT)
            else:
                snap.ensure(state=state, classic=classic, channel=channel, cohort=cohort)
            snaps["success"].append(snap)
        except PackageError:
            snaps["failed"].append(s)

    if len(snaps["failed"]):
        raise PackageError(
            f"Failed to install or refresh snap(s): {', '.join([s for s in snaps['failed']])}"
        )

    return snaps["success"] if len(snaps["success"]) > 1 else snaps["success"][0]


def install_local(
    filename: str,
    classic: Optional[bool] = False,
    devmode: Optional[bool] = False,
    dangerous: Optional[bool] = False,
) -> Snap:
    """Perform a snap operation.

    Args:
        filename: The path to a local .snap file to install.
        classic: Whether to use classic confinement.
        dangerous: Whether --dangerous should be passed to install snaps without a signature.
        devmode: Whether --devmode should be passed to install snap with devmode confinement.

    Raises:
        PackageError: If there is a problem encountered.
    """
    _cmd = [
        "snap",
        "install",
        filename,
    ]
    if classic:
        _cmd.append("--classic")
    if devmode:
        _cmd.append("--devmode")
    if dangerous:
        _cmd.append("--dangerous")
    try:
        result = subprocess.check_output(_cmd, universal_newlines=True).splitlines()[-1]
        snap_name, _ = result.split(" ", 1)
        snap_name = ansi_filter.sub("", snap_name)

        c = SnapCache()

        return c[snap_name]
    except CalledProcessError as e:
        raise PackageError(f"Could not install snap {filename}: {e.output}")


def connect(
    plug_snap: str, plug: str, slot_snap: str = None, slot: str = None, wait: bool = True
) -> None:
    """Connect a snap plug to a slot."""
    _cmd = ["snap", "connect", f"{plug_snap}:{plug}"]
    if slot_snap is not None and slot is not None:
        _cmd.append(f"{slot_snap}:{slot}")
    if slot_snap is not None and slot is None:
        _cmd.append(slot_snap)
    if slot_snap is None and slot is not None:
        _cmd.append(f":{slot}")
    if not wait:
        _cmd.append("--no-wait")

    try:
        subprocess.check_output(_cmd, universal_newlines=True)
    except subprocess.CalledProcessError:
        raise PackageError(f"Failed to connect. Command used: {' '.join(_cmd)}")


def _system_set(config_item: str, value: str) -> None:
    """Helper for setting snap system config values.

    Args:
        config_item: Name of snap system setting. E.g. 'refresh.hold'.
        value: Value to assign.
    """
    _cmd = ["snap", "set", "system", f"{config_item}={value}"]
    try:
        subprocess.check_call(_cmd, universal_newlines=True)
    except CalledProcessError:
        raise PackageError(f"Failed setting system config '{config_item}' to '{value}'")


def hold_refresh(days: int = 90) -> None:
    """Set the system-wide snap refresh hold.

    Args:
        days: Number of days to hold system refreshes for. Maximum 90. Set to zero to remove hold.
    """
    # Currently the snap daemon can only hold for a maximum of 90 days
    if not type(days) == int or days > 90:
        raise ValueError(f"Days must be an int between 1 and 90. Not {days}.")
    elif days == 0:
        _system_set("refresh.hold", "")
    else:
        # Add the number of days to current time
        target_date = datetime.now(timezone.utc).astimezone() + timedelta(days=days)
        # Format for the correct datetime format
        hold_date = target_date.strftime("%Y-%m-%dT%H:%M:%S%z")
        # Python dumps the offset in format '+0100', we need '+01:00'
        hold_date = "{0}:{1}".format(hold_date[:-2], hold_date[-2:])
        # Actually set the hold date
        _system_set("refresh.hold", hold_date)
