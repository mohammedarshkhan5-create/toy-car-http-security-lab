import hashlib
import hmac
import json
import os
import time

import wire


# --------------------------------------------------------------------------- #
# SETTINGS
# --------------------------------------------------------------------------- #

SHARED_SECRET = b"student-car-secret-9f4a2c7e"

PROPERTIES = {
    "Integrity": True,
    "Confidentiality": True,
    "Authentication": True,
    "Authorization": True,
    "Freshness": True,
}

USER_ACTIONS = {
    "student": {"move"},
}


# --------------------------------------------------------------------------- #
# PASSWORD STORAGE
# --------------------------------------------------------------------------- #

PASSWORD_SALT = b"student-password-salt-v1"

PASSWORDS = {
    "student": hashlib.pbkdf2_hmac(
        "sha256",
        b"racecar",
        PASSWORD_SALT,
        200_000
    ).hex()
}


# --------------------------------------------------------------------------- #
# CRYPTOGRAPHIC HELPERS
# --------------------------------------------------------------------------- #

def _password_hash(password):
    return hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        PASSWORD_SALT,
        200_000
    ).hex()


def _keystream(nonce, length):
    result = b""
    counter = 0

    while len(result) < length:
        block = hmac.new(
            SHARED_SECRET,
            nonce.encode("utf-8") + counter.to_bytes(4, "big"),
            hashlib.sha256
        ).digest()

        result += block
        counter += 1

    return result[:length]


def _encrypt(text, nonce):
    data = text.encode("utf-8")
    stream = _keystream(nonce, len(data))

    encrypted = bytes(
        a ^ b for a, b in zip(data, stream)
    )

    return encrypted.hex()


def _decrypt(ciphertext, nonce):
    data = bytes.fromhex(ciphertext)
    stream = _keystream(nonce, len(data))

    decrypted = bytes(
        a ^ b for a, b in zip(data, stream)
    )

    return decrypted.decode("utf-8")


def _message(user, nonce, counter, encrypted):
    return (
        user
        + "|"
        + nonce
        + "|"
        + str(counter)
        + "|"
        + encrypted
    ).encode("utf-8")


def _mac(user, nonce, counter, encrypted):
    return hmac.new(
        SHARED_SECRET,
        _message(user, nonce, counter, encrypted),
        hashlib.sha256
    ).hexdigest()


# --------------------------------------------------------------------------- #
# 1. CLIENT
# --------------------------------------------------------------------------- #

def create_request(command, user, client_state):
    """
    Create an encrypted, authenticated and fresh request.
    """

    # Maintain a request sequence number on the client.
    counter = client_state.get("counter", 0) + 1
    client_state["counter"] = counter

    # New random nonce for every request.
    nonce = os.urandom(16).hex()

    # Password is supplied by the simulator through client_state.
    password = client_state.get("password", "")

    # Encrypt both command and password.
    plaintext = json.dumps(
        {
            "command": command,
            "password": password,
        },
        separators=(",", ":")
    )

    encrypted = _encrypt(plaintext, nonce)

    # Authenticate everything important.
    tag = _mac(
        user,
        nonce,
        counter,
        encrypted
    )

    headers = {
        "X-User": user,
        "X-Nonce": nonce,
        "X-Counter": str(counter),
        "X-Auth": tag,
    }

    body = json.dumps(
        {
            "data": encrypted
        },
        separators=(",", ":")
    )

    return wire.new_request(
        path="/car/command",
        headers=headers,
        body=body
    )


# --------------------------------------------------------------------------- #
# 2. CAR SERVER
# --------------------------------------------------------------------------- #

def verify_request(request, server_state):
    """
    Verify:
      - user
      - request structure
      - freshness
      - HMAC integrity
      - encrypted data
      - password
      - command
    """

    user = wire.header(request, "X-User")
    nonce = wire.header(request, "X-Nonce")
    counter_text = wire.header(request, "X-Counter")
    received_tag = wire.header(request, "X-Auth")

    # Required headers.
    if not user:
        return {
            "ok": False,
            "reason": "missing user"
        }

    if not nonce:
        return {
            "ok": False,
            "reason": "missing nonce"
        }

    if not counter_text:
        return {
            "ok": False,
            "reason": "missing counter"
        }

    if not received_tag:
        return {
            "ok": False,
            "reason": "missing authentication tag"
        }

    # Only known accounts can authenticate.
    if user not in PASSWORDS:
        return {
            "ok": False,
            "reason": "unknown user"
        }

    # Counter must be a valid integer.
    try:
        counter = int(counter_text)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "reason": "invalid counter"
        }

    if counter <= 0:
        return {
            "ok": False,
            "reason": "invalid counter"
        }

    # Read encrypted body.
    try:
        body = wire.json_body(request)
        encrypted = str(body.get("data", ""))
    except Exception:
        return {
            "ok": False,
            "reason": "invalid body"
        }

    if not encrypted:
        return {
            "ok": False,
            "reason": "missing encrypted data"
        }

    # --------------------------------------------------------------------- #
    # FRESHNESS
    # --------------------------------------------------------------------- #

    last_counter = server_state.get("last_counter", 0)

    # Every request must be newer than the previous accepted request.
    #
    # This blocks:
    #   F -> F replay
    #   F -> L -> old F
    #   delayed old requests
    if counter <= last_counter:
        return {
            "ok": False,
            "reason": "stale or replayed request"
        }

    # --------------------------------------------------------------------- #
    # INTEGRITY + AUTHENTICATION
    # --------------------------------------------------------------------- #

    expected_tag = _mac(
        user,
        nonce,
        counter,
        encrypted
    )

    if not hmac.compare_digest(
        received_tag,
        expected_tag
    ):
        return {
            "ok": False,
            "reason": "invalid authentication tag"
        }

    # Only advance the server counter after authentication succeeds.
    server_state["last_counter"] = counter

    # --------------------------------------------------------------------- #
    # DECRYPT
    # --------------------------------------------------------------------- #

    try:
        plaintext = _decrypt(
            encrypted,
            nonce
        )

        data = json.loads(plaintext)

    except Exception:
        return {
            "ok": False,
            "reason": "invalid encrypted data"
        }

    command = str(
        data.get("command", "")
    ).upper()

    password = str(
        data.get("password", "")
    )

    # --------------------------------------------------------------------- #
    # COMMAND VALIDATION
    # --------------------------------------------------------------------- #

    valid_commands = {
        "F",
        "B",
        "L",
        "R",
        "ADMIN_RESET"
    }

    if command not in valid_commands:
        return {
            "ok": False,
            "reason": "invalid command"
        }

    # --------------------------------------------------------------------- #
    # PASSWORD AUTHENTICATION
    # --------------------------------------------------------------------- #

    supplied_hash = _password_hash(password)
    stored_hash = PASSWORDS.get(user)

    if not hmac.compare_digest(
        supplied_hash,
        stored_hash
    ):
        return {
            "ok": False,
            "reason": "wrong password"
        }

    return {
        "ok": True,
        "user": user,
        "command": command
    }


# --------------------------------------------------------------------------- #
# 3. AUTHORIZATION
# --------------------------------------------------------------------------- #

def authorize(user, action, server_state):
    """
    student -> move only
    """

    allowed = USER_ACTIONS.get(
        user,
        set()
    )

    return action in allowed


# --------------------------------------------------------------------------- #
# 4. MAINTENANCE DOOR
# --------------------------------------------------------------------------- #

def maintenance_auth(request, server_state):
    """
    The student account must never be able to authenticate through
    the maintenance door.

    Returning immediately also avoids timing differences.
    """

    return {
        "ok": False
    }