"""The built-in protocol used by the pre-set scenarios.

Each scenario switches a few options on or off; the request format stays the
same shape throughout, so a request captured in one scenario is still readable
in the next one.

    headers   X-User        who the request claims to be from
              X-Pass        password, when the scenario asks for one
              X-Digest      hex digest over the body text
              X-Digest-Alg  which algorithm produced X-Digest
    body      {"command": "F"}            or
              {"enc": "<hex>"}            when the scenario encodes the body

Not every scenario looks at every field.  Which ones it looks at is exactly
what the class is about.

WARNING - teaching code.  The XOR transform below is NOT encryption: it is a
repeating-key byte flip, breakable with pencil and paper, and it protects
nothing.  It is here only so that the body stops being readable text in the
interceptor panel.  Real systems use TLS (AES-GCM / ChaCha20-Poly1305).

You do not need to edit this file - the last scenario runs student_solution.py.
"""

import hashlib
import hmac
import json
import os
import random
import secrets
import time

import labusers
import wire

# Secrets held by the client and the car server.  The interceptor never imports
# this module, so it does not get these for free.
SHARED_SECRET = b"toycar-shared-secret"
XOR_SECRET = b"toycar-xor-secret"

# Maintenance access code (fake, for this project only).  It is drawn when the program
# starts and stays put until it is restarted, so it cannot be looked up in the
# source.  Set TOYCAR_MAINTENANCE_CODE to pin it.
MAINTENANCE_ALPHABET = "0123456789"
MAINTENANCE_LENGTH = 5

# The identity a scenario without accounts sends.
SINGLE_DRIVER = "driver"


def _draw_maintenance_code():
    chosen = os.environ.get("TOYCAR_MAINTENANCE_CODE", "").strip()
    if chosen:
        return chosen
    return "".join(secrets.choice(MAINTENANCE_ALPHABET)
                   for _ in range(MAINTENANCE_LENGTH))


MAINTENANCE_CODE = _draw_maintenance_code()

PLAIN_ALGS = {"sha256": "sha256", "sha1": "sha1", "md5": "md5"}
SECRET_ALGS = {"hmac-sha256"}


# --------------------------------------------------------------------------- #
# small primitives
# --------------------------------------------------------------------------- #
def digest(alg, text, secret=None):
    """Hex digest of `text` under `alg`, or None if the algorithm is unknown."""
    data = text.encode("utf-8") if isinstance(text, str) else text
    alg = (alg or "").lower()
    if alg == "hmac-sha256":
        if secret is None:
            return None
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        return hmac.new(secret, data, hashlib.sha256).hexdigest()
    if alg in PLAIN_ALGS:
        return hashlib.new(PLAIN_ALGS[alg], data).hexdigest()
    return None


def xor_bytes(data):
    return bytes(b ^ XOR_SECRET[i % len(XOR_SECRET)] for i, b in enumerate(data))


def encode_body(payload):
    """dict -> hex text using the repeating-key XOR transform."""
    return xor_bytes(json.dumps(payload).encode("utf-8")).hex()


def decode_body(hex_text):
    """hex text -> dict, or None if it does not decode to a JSON object."""
    try:
        plain = xor_bytes(bytes.fromhex((hex_text or "").strip()))
        data = json.loads(plain.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def equal(a, b):
    """Compare two strings for equality."""
    return hmac.compare_digest(str(a), str(b))


def compare_codes(reference, entered, pause=0.0, variation=0.0):
    """Return True if the entered maintenance code matches the reference."""
    for expected, supplied in zip(reference, entered):
        if pause:
            time.sleep(pause + (random.random() * variation if variation else 0.0))
        if expected != supplied:
            return False
    return len(reference) == len(entered)


# --------------------------------------------------------------------------- #
# the built-in protocol
# --------------------------------------------------------------------------- #
class LabProtocol:
    """One configuration of the built-in protocol.

    Options (all default off):
        digest_mode   ""            no X-Digest at all
                      "plain"       X-Digest with sha256 / sha1 / md5
                      "hmac"        X-Digest with hmac-sha256
        encode_body   True          put the payload through the XOR transform
        require_auth  True          require X-User / X-Pass to match an account
        enforce_authz True          check each action against the account
        skip_authz    {"admin_reset"}  actions the server does not check
        maintenance   "quick" | "paced"   how the maintenance door answers
    """

    def __init__(self, digest_mode="", encode_body=False, require_auth=False,
                 enforce_authz=False, skip_authz=(),
                 maintenance="quick", response_pause=0.300,
                 response_variation=0.0):
        self.digest_mode = digest_mode
        self.encode_body = encode_body
        self.require_auth = require_auth
        self.enforce_authz = enforce_authz
        # Accounts are part of the lesson only once one of these is on.  Until
        # then the car has a single driver and the client panel says so.
        self.accounts = bool(require_auth or enforce_authz)
        self.skip_authz = set(skip_authz)
        self.maintenance = maintenance
        # Whether the Client panel offers the maintenance door at all.
        self.maintenance_door = maintenance == "paced"
        self.response_pause = response_pause
        self.response_variation = response_variation
        self.default_alg = ("hmac-sha256" if digest_mode == "hmac"
                            else "sha256")

    # -- client side -------------------------------------------------------- #
    def create_request(self, command, user, client_state):
        """Build the request this client sends over the network."""
        payload = {"command": command}
        body = (json.dumps({"enc": encode_body(payload)}) if self.encode_body
                else json.dumps(payload))

        headers = {"X-User": user if self.accounts else SINGLE_DRIVER}
        if self.require_auth:
            headers["X-Pass"] = client_state.get("password", "")
        if self.digest_mode:
            alg = client_state.get("alg") or self.default_alg
            secret = SHARED_SECRET if alg in SECRET_ALGS else None
            headers["X-Digest-Alg"] = alg
            headers["X-Digest"] = digest(alg, body, secret) or ""
        return wire.new_request(path="/car/command", headers=headers, body=body)

    # -- car server side ---------------------------------------------------- #
    def verify_request(self, request, server_state):
        """Check one arriving request.

        Returns {"ok": True, "user": ..., "command": ...}
             or {"ok": False, "reason": ...}
        """
        body = request.get("body") or ""
        user = wire.header(request, "X-User")

        if self.digest_mode:
            alg = (wire.header(request, "X-Digest-Alg")
                   or self.default_alg).lower()
            allowed = (SECRET_ALGS if self.digest_mode == "hmac"
                       else set(PLAIN_ALGS))
            if alg not in allowed:
                return {"ok": False, "reason": f"algorithm {alg!r} not accepted"}
            secret = SHARED_SECRET if alg in SECRET_ALGS else None
            want = digest(alg, body, secret)
            if want is None or not equal(want, wire.header(request, "X-Digest")):
                return {"ok": False, "reason": f"{alg} digest did not match"}

        data = wire.json_body(request)
        if "enc" in data:
            data = decode_body(str(data.get("enc", ""))) or {}
            if not data:
                return {"ok": False, "reason": "body did not decode"}
        elif self.encode_body:
            return {"ok": False, "reason": "body was not encoded"}

        command = str(data.get("command", "")).upper()
        if not command:
            return {"ok": False, "reason": "no command in body"}

        if self.require_auth:
            if not labusers.check_password(user, wire.header(request, "X-Pass")):
                return {"ok": False, "reason": "account or password not accepted"}
        elif user not in labusers.USERS:
            user = user or "student"

        return {"ok": True, "user": user, "command": command}

    def authorize(self, user, action, server_state):
        """True if `user` may perform `action`."""
        if not self.enforce_authz:
            return True
        if action in self.skip_authz:
            return True
        return labusers.may(user, action)

    # -- separate maintenance endpoint -------------------------------------- #
    def maintenance_auth(self, request, server_state):
        """Check the maintenance access code. Returns {"ok": bool}."""
        guess = str(wire.json_body(request).get("code", ""))
        if self.maintenance == "paced":
            ok = compare_codes(MAINTENANCE_CODE, guess,
                               pause=self.response_pause,
                               variation=self.response_variation)
        else:
            ok = equal(MAINTENANCE_CODE, guess)
        return {"ok": bool(ok)}

    # -- what the server panel shows ---------------------------------------- #
    def properties(self):
        return {
            "Integrity": bool(self.digest_mode == "hmac"),
            "Confidentiality": bool(self.encode_body),
            "Authentication": bool(self.require_auth),
            "Authorization": bool(self.enforce_authz and not self.skip_authz),
            # No built-in scenario provides this one.
            "Freshness": False,
        }


def load_student_module():
    """Read student_solution.py from disk and run it as a fresh module.

    A plain `import` would hand back the copy Python already has in memory, so
    an edit would not show up until the whole program was restarted.  Building
    a new module object each time means Reset Scenario, and each check run,
    see the file exactly as it is saved right now.
    """
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "student_solution.py")
    spec = importlib.util.spec_from_file_location("student_solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StudentProtocol:
    """Adapter so `student_solution.py` plugs in wherever LabProtocol does."""

    def __init__(self, module=None):
        self.module = module if module is not None else load_student_module()

    def create_request(self, command, user, client_state):
        return self.module.create_request(command, user, client_state)

    def verify_request(self, request, server_state):
        result = self.module.verify_request(request, server_state)
        return result if isinstance(result, dict) else {"ok": False,
                                                        "reason": "no result"}

    def authorize(self, user, action, server_state):
        return bool(self.module.authorize(user, action, server_state))

    def maintenance_auth(self, request, server_state):
        fn = getattr(self.module, "maintenance_auth", None)
        if fn is None:
            guess = str(wire.json_body(request).get("code", ""))
            return {"ok": equal(MAINTENANCE_CODE, guess)}
        result = fn(request, server_state)
        return result if isinstance(result, dict) else {"ok": bool(result)}

    def properties(self):
        claimed = getattr(self.module, "PROPERTIES", None)
        if isinstance(claimed, dict):
            return {k: bool(v) for k, v in claimed.items()}
        return {}

    def reload(self):
        self.module = load_student_module()
