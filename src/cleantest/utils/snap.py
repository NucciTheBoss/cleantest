#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
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
from typing import Any, Callable, Dict, Iterable, List, Union

# Filter for extracting 7-bit C1 ANSI sequences from a string.
ansi_filter = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class SnapHandlerError(Exception):
    """Raised when snap handler encounters any errors."""


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


def _cache_init(func: Callable):
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
        daemon: str = None,
        daemon_scope: str = None,
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
        apps: List[Dict[str, str]] = None,
        cohort: str = "",
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

    def _snap(self, command: str, optargs: Iterable[str] = None) -> str:
        """Perform a snap operation.

        Args:
            command (str): The snap command to execute
            optargs (Iterable[str]): A list of additional arguments to pass,
                commonly confinement or channel

        Raises:
          SnapHandlerError: Raised there is a problem encountered when executing snap command.

        Returns:
            (str): Captured output of operation performed on snap.
        """
        optargs = optargs or []
        _cmd = ["snap", command, self._name, *optargs]
        try:
            return subprocess.check_output(_cmd, universal_newlines=True)
        except CalledProcessError as e:
            raise SnapHandlerError(
                f"Snap: {self._name}; command {_cmd} failed with output = {e.output}"
            )

    def _snap_daemons(
        self,
        command: List[str],
        services: List[str] = None,
    ) -> CompletedProcess:
        """Execute command on a list of snap services.

        Args:
            command (List[str]): Command to execute on snap services.
            services (List[str]): Services to operate on (Default: None).

        Returns:
            (CompletedProcess): Captured output of operation on snap services.
        """
        if services:
            # an attempt to keep the command constrained to the snap instance's services
            services = [f"{self._name}.{service}" for service in services]
        else:
            services = [self._name]

        _cmd = ["snap", *command, *services]

        try:
            return subprocess.run(
                _cmd, universal_newlines=True, check=True, capture_output=True
            )
        except CalledProcessError as e:
            raise SnapHandlerError(
                f"Could not {_cmd} for snap [{self._name}]: {e.stderr}"
            )

    def get(self, key) -> str:
        """Gets a snap configuration value.

        Args:
            key (str): The key to retrieve.

        Returns:
            (str): Captured output of get operation.
        """
        return self._snap("get", [key]).strip()

    def set(self, config: Dict) -> str:
        """Sets a snap configuration value.

        Args:
           config (Dict): A dictionary containing keys and values specifying the config to set.

        Returns:
            (str): Captured output of set operation.
        """
        args = [f'{key}="{val}"' for key, val in config.items()]

        return self._snap("set", [*args])

    def unset(self, key: str) -> str:
        """Unsets a snap configuration value.

        Args:
            key (str): The key to unset.

        Returns:
            (str): Captured output of unset operation.
        """
        return self._snap("unset", [key])

    def start(self, services: List[str] = None, enable: bool = False) -> None:
        """Starts a snap's services.

        Args:
            services (List[str]): List of individual snap services to start,
                otherwise all (Default: None).
            enable (bool): Flag to enable snap services on start (Default: False).
        """
        args = ["start", "--enable"] if enable else ["start"]
        self._snap_daemons(args, services)

    def stop(self, services: List[str] = None, disable: bool = False) -> None:
        """Stops a snap's services.

        Args:
            services (List[str]): List of individual snap services to stop,
                otherwise all (Default: None).
            disable (bool): Flag to disable snap services on stop (Default: False).
        """
        args = ["stop", "--disable"] if disable else ["stop"]
        self._snap_daemons(args, services)

    def logs(self, services: List[str] = None, num_lines: int = 10) -> str:
        """Shows a snap services' logs.

        Args:
            services (List[str]): List of individual snap services to show logs from,
                otherwise all (Default: None).
            num_lines (int): Integer number of log lines to return (Default: 10).

        Returns:
            (str): Captured output of logs operation.
        """
        args = ["logs", f"-n={num_lines}"] if num_lines else ["logs"]
        return self._snap_daemons(args, services).stdout

    def restart(self, services: List[str] = None, reload: bool = False) -> None:
        """Restarts a snap's services.

        Args:
            services (list): List of individual snap services to restart,
                otherwise all (Default: None).
            reload (bool): Flag to use the service reload command, if available (Default: False).
        """
        args = ["restart", "--reload"] if reload else ["restart"]
        self._snap_daemons(args, services)

    def _install(self, channel: str = "", cohort: str = "") -> None:
        """Add a snap to the system.

        Args:
            channel (str): The channel to install from (Default: "").
            cohort (str): The key of a cohort that this snap belongs to (Default: "").
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
        channel: str = "",
        cohort: str = "",
        leave_cohort: bool = False,
    ) -> None:
        """Refresh a snap.

        Args:
            channel (str): The channel to install from (Default: "").
            cohort (str): Specify a cohort (Default: "").
            leave_cohort (bool): Leave the current cohort (Default: False).
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
        """Removes a snap from the system.

        Returns:
            (str): Captured output of remove operation.
        """
        return self._snap("remove")

    @property
    def name(self) -> str:
        """Get the name of the snap.

        Returns:
            (str): Name of the snap.
        """
        return self._name

    def ensure(
        self,
        state: SnapState,
        classic: bool = False,
        channel: str = "",
        cohort: str = "",
    ):
        """Ensures that the snap is in a given state.

        Args:
            state (SnapState): A `SnapState` to reconcile to.
            classic (bool): A boolean indicating whether classic confinement should
                be used (Default: False).
            channel (str): The channel to install from (Default: "").
            cohort (str): Specify the key of a snap cohort (Default: "").

        Raises:
            SnapHandlerError: Raised if an error is encountered while
                ensuring that the snap is in a given state.
        """
        self._confinement = (
            "classic" if classic or self._confinement == "classic" else ""
        )

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
        """Get whether a snap is present.

        Returns:
            (bool): True - snap is present. False - snap is not present.
        """
        return self._state in (SnapState.PRESENT, SnapState.LATEST)

    @property
    def latest(self) -> bool:
        """Get whether the snap is the most recent version.

        Returns:
            (bool): True - snap is the most recent version.
                False - snap is not the most recent version.
        """
        return self._state is SnapState.LATEST

    @property
    def state(self) -> SnapState:
        """Get the current snap state.

        Returns:
            (SnapState): Current snap state.
        """
        return self._state

    @state.setter
    def state(self, state: SnapState) -> None:
        """Sets the snap state to a given value.

        Args:
          state (SnapState): A `SnapState` to reconcile the snap to.

        Raises:
          SnapHandlerError: Raised if an error is encountered while setting
            the state of the snap.
        """
        if self._state is not state:
            self.ensure(state)
        self._state = state

    @property
    def revision(self) -> str:
        """Get the revision of the snap.

        Returns:
            (str): Revision of the snap.
        """
        return self._revision

    @property
    def channel(self) -> str:
        """Get the channel of the snap.

        Returns:
            (str): Channel of the snap.
        """
        return self._channel

    @property
    def confinement(self) -> str:
        """Get the confinement of the snap.

        Returns:
            (str): Confinement of the snap.
        """
        return self._confinement

    @property
    def apps(self) -> List:
        """Get the installed apps of the snap.

        Returns:
            (List): Installed apps of the snap, if any.
        """
        self._update_snap_apps()
        return self._apps

    @property
    def services(self) -> Dict:
        """Get the installed services of the snap.

        Returns:
            (Dict): Installed services of the snap, if any.
        """
        self._update_snap_apps()
        services = {}
        for app in self._apps:
            if "daemon" in app:
                services[app["name"]] = SnapService(**app).__dict__

        return services


class _UnixSocketConnection(http.client.HTTPConnection):
    """Implementation of HTTPConnection that connects to a named Unix socket."""

    def __init__(
        self, host: str, timeout: float = None, socket_path: Any = None
    ) -> None:
        if timeout is None:
            super().__init__(host)
        else:
            super().__init__(host, timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
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
        opener: urllib.request.OpenerDirector = None,
        base_url: str = "http://localhost/v2/",
        timeout: float = 5.0,
    ):
        """Initialize a client instance.

        Args:
            socket_path (str): A path to the socket on the filesystem
                (Default: "/run/snap/snapd.socket").
            opener (urllib.request.OpenerDirector): Specifies an opener for unix socket.
                If set to None, a default is used.
            base_url (str): Base url for making requests to the snap client. Defaults to
                (Default: "http://localhost/v2/")
            timeout (float): Timeout in seconds to use when making requests to the API.
                (Default: 5.0).
        """
        if opener is None:
            opener = self._get_default_opener(socket_path)
        self.opener = opener
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    def _get_default_opener(cls, socket_path: str) -> urllib.request.OpenerDirector:
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
    ) -> Union[dict, List]:
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
            raise SnapHandlerError(
                "snapd is not installed or not in /usr/bin"
            ) from None
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
                raise SnapHandlerError(f"Snap '{snap_name}' not found!")

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

    def _load_info(self, name: str) -> Snap:
        """Load info for snaps which are not installed if requested.

        Args:
            name (str): A string representing the name of the snap.
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
    snap_names: Union[str, List[str]],
    state: Union[str, SnapState] = SnapState.LATEST,
    channel: str = "latest",
    classic: bool = False,
    cohort: str = "",
) -> Union[Snap, List[Snap]]:
    """Install a snap or snaps in a remote process.

    Args:
        snap_names (Union[str, List[str]]): The name or names of the snaps to install.
        state (SnapState): A string or `SnapState` representation of the desired state, one of
            [`PRESENT` or `LATEST`] (Default: SnapState.LATEST).
        channel (str): A channel as a string (Default: "latest").
        classic (bool): A boolean specifying whether it should be added with classic
            confinement (Default: False).
        cohort (str): The key of a cohort that this snap belongs to (Default: "").

    Raises:
        SnapHandlerError: Raised if some snaps failed to install or were not found.

    Returns:
        (Union[Snap, List[Snap]]): Result of operation.
    """
    snap_names = [snap_names] if type(snap_names) is str else snap_names
    if not snap_names:
        raise TypeError("Expected at least one snap to add, received zero!")

    if type(state) is str:
        state = SnapState(state)

    return _wrap_snap_operations(snap_names, state, channel, classic, cohort)


@_cache_init
def remove(snap_names: Union[str, List[str]]) -> Union[Snap, List[Snap]]:
    """Removes a snap from the system.

    Args:
        snap_names (Union[str, List[str]]): The name or names of the snaps to remove.

    Raises:
        SnapHandlerError: Raised if some snaps failed to be removed.

    Returns:
        (Union[Snap, List[Snap]]): Result of operation.
    """
    snap_names = [snap_names] if type(snap_names) is str else snap_names
    if not snap_names:
        raise TypeError("Expected at least one snap to add, received zero!")

    return _wrap_snap_operations(snap_names, SnapState.ABSENT, "", False)


@_cache_init
def ensure(
    snap_names: Union[str, List[str]],
    state: str,
    channel: str = "latest",
    classic: bool = False,
    cohort: str = "",
) -> Union[Snap, List[Snap]]:
    """Ensures a snap is in a given state to the system.

    Args:
        snap_names (Union[str, List[str]]): The name(s) of the snaps to operate on.
        state (str): A string representation of the desired state, from `SnapState`.
        channel (str): A channel as a string (Default: "latest").
        classic (bool): A boolean specifying whether it should be added with classic.
            confinement (Default: False).
        cohort (str): The key of a cohort that this snap belongs to (Default: "").

    Raises:
        SnapHandlerError: Raised if the snap is not in the cache.
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
    cohort: str = "",
) -> Union[Snap, List[Snap]]:
    """Wrap common operations for bare snap commands.

    Args:
        snap_names (List[str]): Snaps to perform operations on.
        state (SnapState): State to set snap in.
        channel (str): Channel to track.
        classic (bool): Ensure snap is in classic confinement or not.
        cohort (str): Key of cohort to ensure snap belongs to (Default: "").

    Raises:
        SnapHandlerError: Raised if install or refresh operation fails.
    """
    snaps = {"success": [], "failed": []}

    for s in snap_names:
        try:
            snap = _Cache[s]
            if state is SnapState.ABSENT:
                snap.ensure(state=SnapState.ABSENT)
            else:
                snap.ensure(
                    state=state, classic=classic, channel=channel, cohort=cohort
                )
            snaps["success"].append(snap)
        except SnapHandlerError:
            snaps["failed"].append(s)

    if len(snaps["failed"]):
        raise SnapHandlerError(
            f"Failed to install or refresh snap(s): {', '.join(list(snaps['failed']))}"
        )

    return snaps["success"] if len(snaps["success"]) > 1 else snaps["success"][0]


def install_local(
    filename: str,
    classic: bool = False,
    devmode: bool = False,
    dangerous: bool = False,
) -> Snap:
    """Install snap package using local .snap file.

    Args:
        filename (str): The path to a local .snap file to install.
        classic (bool): Whether --classic should be passed to
            install snap with classic confinement (Default: False).
        dangerous (bool): Whether --dangerous should be passed to
            install snap without a signature (Default: False).
        devmode (bool): Whether --devmode should be passed to
            install snap with devmode confinement (Default: False).

    Raises:
        SnapHandlerError: Raised if local .snap package fails to install.
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
        raise SnapHandlerError(f"Could not install snap {filename}: {e.output}")


def alias(alias_snap: str, app: str, alias: str, wait: bool = True) -> None:
    """Add an alias for a snap command.

    Args:
        alias_snap (str): Snap that provides the app that an alias will be created for.
        app (str): App inside snap package to create alias for.
        alias (str): Alias to create.
        wait (bool):
            True - wait for alias operation to finish.
            False - do not wait for alias operation to finish (Default: True).

    Raises:
        SnapHandlerError: Raised if alias operation fails.
    """
    _cmd = ["snap", "alias", f"{alias_snap}.{app}", alias]
    if not wait:
        _cmd.append("--no-wait")

    try:
        subprocess.check_output(_cmd, universal_newlines=True)
    except subprocess.CalledProcessError:
        raise SnapHandlerError(
            f"Failed to create alias. Command used: {' '.join(_cmd)}"
        )


def unalias(alias_snap: str, wait: bool = True) -> None:
    """Remove an alias for a snap command.

    Args:
        alias_snap (str): Snap to remove aliases from..
        wait (bool):
            True - wait for unalias operation to finish.
            False - do not wait for unalias operation to finish (Default: True).

    Raises:
        SnapHandlerError: Raised if unalias operation fails.
    """
    _cmd = ["snap", "unalias", alias_snap]
    if not wait:
        _cmd.append("--no-wait")

    try:
        subprocess.check_output(_cmd, universal_newlines=True)
    except subprocess.CalledProcessError:
        raise SnapHandlerError(
            f"Failed to destroy alias. Command used: {' '.join(_cmd)}"
        )


def connect(
    plug: str,
    plug_snap: str,
    slot_snap: str = None,
    slot: str = None,
    wait: bool = True,
) -> None:
    """Connect a snap plug to a slot.

    Args:
        plug (str): Plug to connect to slot.
        plug_snap (str): Snap that provides plug.
        slot_snap (str): Snap that provides slot (Default: None).
        slot (str): Slot to connect to (Default: None).
        wait (bool):
            True - wait for connect operation to finish.
            False - do not wait for connect operation to finish (Default: True).

    Raises:
        SnapHandlerError: Raised if connect operation fails.
    """
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
        raise SnapHandlerError(f"Failed to connect. Command used: {' '.join(_cmd)}")


def disconnect(
    plug: str,
    plug_snap: str = None,
    slot_snap: str = None,
    slot: str = None,
    wait: bool = True,
    forget: bool = False,
) -> None:
    """Disconnect a snap plug from a slot.

    Args:
        plug (str): Plug to disconnect from slot.
        plug_snap (str): Snap that provides plug (Default: None).
        slot_snap (str): Snap that provides slot (Default: None).
        slot (str): Slot to disconnect from (Default: None).
        wait (bool):
            True - wait for disconnect operation to finish.
            False - do not wait for disconnect operation to finish (Default: True).
        forget (bool):
            True - forget remembered state about connection.
            False - do not forget remember state about connection (Default: False).

    Raises:
        SnapHandlerError: Raised if disconnect operation fails.
    """
    _cmd = ["snap", "disconnect", f":{plug}"]
    if plug_snap is not None:
        _cmd[2] = f"{plug_snap}:{plug}"
    if slot_snap is not None and slot is not None:
        _cmd.append(f"{slot_snap}:{slot}")
    if not wait:
        _cmd.append("--no-wait")
    if forget:
        _cmd.append("--forget")

    try:
        subprocess.check_output(_cmd, universal_newlines=True)
    except subprocess.CalledProcessError:
        raise SnapHandlerError(
            f"Failed to create alias. Command used: {' '.join(_cmd)}"
        )


def _system_set(config_item: str, value: str) -> None:
    """Helper for setting snap system config values.

    Args:
        config_item (str): Name of snap system setting. E.g. 'refresh.hold'.
        value (str): Value to assign.

    Raises:
        SnapHandlerError: Raised if system set operation fails.
    """
    _cmd = ["snap", "set", "system", f"{config_item}={value}"]
    try:
        subprocess.check_call(_cmd, universal_newlines=True)
    except CalledProcessError:
        raise SnapHandlerError(
            f"Failed setting system config '{config_item}' to '{value}'"
        )


def hold_refresh(days: int = 90) -> None:
    """Set the system-wide snap refresh hold.

    Args:
        days (int): Number of days to hold system refreshes for. Maximum 90.
            Set to zero to remove hold.

    Warnings:
        This method does not currently support snap's experimental `--hold` feature.
    """
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
