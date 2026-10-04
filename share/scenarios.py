"""Scenario table plus the live session state.

A scenario is just a named configuration of a protocol object, so a class can
start from the same place the video started from.  "Reset Scenario" rebuilds
that protocol, empties the client and server memory, clears the monitor log
and puts the car back in the middle.


You do not need to edit this file.
"""

import threading

import carsim
import protocol

SCENARIOS = [
    {
        "id": "direct",
        "name": "Client and car",
        "summary": "Only the Client and the Car server. Nobody in between.",
        "interceptor": False,
        "make": lambda: protocol.LabProtocol(),
    },
    {
        "id": "plain",
        "name": "Plain HTTP",
        "summary": "The same requests as scenario 0, with the Interceptor in between.",
        "make": lambda: protocol.LabProtocol(),
    },
    {
        "id": "hash",
        "name": "Hash",
        "summary": "Each request carries a digest of its body that uses no secret.",
        "make": lambda: protocol.LabProtocol(digest_mode="plain"),
    },
    {
        "id": "encryption",
        "name": "Encryption",
        "summary": "The body is transformed before it is sent.",
        "make": lambda: protocol.LabProtocol(encode_body=True),
    },
    {
        "id": "access",
        "name": "Authentication / Access Control",
        "summary": "The account signs in with a password before the car obeys.",
        "make": lambda: protocol.LabProtocol(digest_mode="hmac",
                                             require_auth=True,
                                             enforce_authz=True,
                                             skip_authz={"admin_reset"}),
    },
    {
        "id": "maintenance",
        "name": "Maintenance access",
        "summary": "A separate maintenance door accepts a five-digit "
                   "access code.",
        "make": lambda: protocol.LabProtocol(digest_mode="hmac",
                                             require_auth=True,
                                             enforce_authz=True,
                                             maintenance="paced"),
    },
    {
        "id": "student",
        "name": "Student Solution",
        "summary": "Runs student_solution.py and nothing else.",
        "make": lambda: protocol.StudentProtocol(),
    },
]

# The number shown to students is the position in this list, counting from 0,
# so the table and the prose in the README can never drift apart again.
for _i, _s in enumerate(SCENARIOS):
    _s["name"] = f"{_i} · {_s['name']}"
    _s.setdefault("interceptor", True)

BY_ID = {s["id"]: s for s in SCENARIOS}
DEFAULT = "direct"


class Session:
    """Which scenario is loaded, plus the two memories it is allowed to keep."""

    def __init__(self, scenario_id=DEFAULT):
        self.lock = threading.Lock()
        self.options = {"jitter": False}
        self.scenario_id = scenario_id if scenario_id in BY_ID else DEFAULT
        self.client_state = {}
        self.server_state = {}
        self.protocol = None
        self.error = ""
        self._build()

    # -- lifecycle ---------------------------------------------------------- #
    def _build(self):
        self.error = ""
        try:
            self.protocol = BY_ID[self.scenario_id]["make"]()
        except Exception as exc:                      # a broken student file
            self.protocol = protocol.LabProtocol()
            self.error = f"{type(exc).__name__}: {exc}"
        jitter = 0.02 if self.options.get("jitter") else 0.0
        if hasattr(self.protocol, "response_variation"):
            self.protocol.response_variation = jitter

    def select(self, scenario_id):
        if scenario_id not in BY_ID:
            return False
        with self.lock:
            self.scenario_id = scenario_id
        self.reset()
        return True

    def reset(self):
        """Back to the starting state of the current scenario."""
        with self.lock:
            self.client_state = {}
            self.server_state = {}
            self._build()
        carsim.reset()

    def set_option(self, name, value):
        with self.lock:
            self.options[name] = bool(value)
            self._build()

    @property
    def has_interceptor(self):
        return bool(BY_ID[self.scenario_id]["interceptor"])

    # -- description for the UI --------------------------------------------- #
    def info(self):
        meta = BY_ID[self.scenario_id]
        try:
            props = self.protocol.properties()
        except Exception:
            props = {}
        return {
            "id": self.scenario_id,
            "name": meta["name"],
            "summary": meta["summary"],
            # Scenario 0 has no Interceptor panel at all.
            "interceptor": meta["interceptor"],
            "properties": props,
            # Accounts are only part of the page once a scenario uses them.
            "accounts": bool(getattr(self.protocol, "accounts", True)),
            # The maintenance door is only on the page where it exists.
            "maintenance": bool(getattr(self.protocol,
                                        "maintenance_door", True)),
            "options": dict(self.options),
            "error": self.error,
            "scenarios": [{"id": s["id"], "name": s["name"],
                           "summary": s["summary"]} for s in SCENARIOS],
        }
