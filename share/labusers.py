"""The one account the car server knows.

NOTHING IN THIS FILE IS A REAL CREDENTIAL.  The account exists only inside
this teaching simulator.  Never reuse the password anywhere.

The password is stored here as an unsalted SHA-256 hex digest, which is the
storage format the built-in scenarios use.  It is deliberately a very
common word so that the class password-cracking exercise has something to
work on.

The car also understands ADMIN_RESET (the "Workshop reset" command).  No
driver account may send it: it belongs to the workshop, not to the person
holding the controller.


You do not need to edit this file.
"""

import hashlib

# user -> permitted actions (see carsim.ACTION_OF for the action names)
PERMISSIONS = {
    "student": {"move"},
}

# The password.  Kept in the source so the class can see both sides.
LAB_PASSWORDS = {
    "student": "racecar",
}

# The account whose digest is handed out for the cracking exercise.
EXPORT_USERS = ["student"]

USERS = ["student"]


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# user -> stored password digest
PASSWORD_HASHES = {u: sha256_hex(p) for u, p in LAB_PASSWORDS.items()}


def check_password(user, password):
    """True if `password` matches the stored digest for `user`."""
    stored = PASSWORD_HASHES.get(user)
    if not stored:
        return False
    return sha256_hex(password or "") == stored


def permissions(user):
    return set(PERMISSIONS.get(user, set()))


def may(user, action):
    return action in PERMISSIONS.get(user, set())


def hash_export():
    """One digest per line, for the offline cracking exercise.

    Nothing else goes in this file: a hash list has no comment syntax, and a
    `user:` prefix needs an extra flag, so either one would stop the exercise
    running as documented.  The hint about what these are lives in the Server
    panel and the README instead.
    """
    return "".join(f"{PASSWORD_HASHES[user]}\n" for user in EXPORT_USERS)
