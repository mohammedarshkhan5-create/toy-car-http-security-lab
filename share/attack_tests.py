#!/usr/bin/env python3
"""Attack tests.

Runs a fixed set of attacks against a protocol and prints one line per attack.
PASS means the attack did not get what it wanted.  FAIL means it did.

    python3 attack_tests.py                 test student_solution.py
    python3 attack_tests.py --scenario access test a built-in scenario
    python3 attack_tests.py --verbose       show what each attack sent

The attacker in here only ever touches the raw request text, exactly like the
Interceptor panel does.

You run this file; you do not need to edit it.
"""

import json
import statistics
import sys
import time

import carsim
import labusers
import protocol
import scenarios
import wire

VERBOSE = False


# --------------------------------------------------------------------------- #
# a stand-in for the car server, without the HTTP layer
# --------------------------------------------------------------------------- #
class Target:
    def __init__(self, proto):
        self.proto = proto
        self.server_state = {}
        self.client_state = {}

    def client_request(self, command, user="student"):
        self.client_state["password"] = labusers.LAB_PASSWORDS.get(user, "")
        self.client_state["user"] = user
        request = self.proto.create_request(command, user, self.client_state)
        return wire.to_wire(request)

    def send(self, text):
        """Returns (accepted, command_applied, user)."""
        request = wire.from_wire(text)
        if request is None:
            return False, "", ""
        try:
            checked = self.proto.verify_request(request, self.server_state)
        except Exception:
            return False, "", ""
        if not isinstance(checked, dict) or not checked.get("ok"):
            return False, "", ""
        user = str(checked.get("user", ""))
        command = str(checked.get("command", "")).upper()
        action = carsim.ACTION_OF.get(command)
        if action is None:
            return False, "", user
        try:
            if not self.proto.authorize(user, action, self.server_state):
                return False, "", user
        except Exception:
            return False, "", user
        return True, command, user

    def maintenance(self, code):
        request = wire.new_request(path="/maintenance/auth",
                                   body=json.dumps({"code": code}))
        started = time.perf_counter()
        try:
            result = self.proto.maintenance_auth(request, self.server_state)
        except Exception:
            result = {"ok": False}
        return bool(result.get("ok")), (time.perf_counter() - started) * 1000.0


def edit_body(text, replace_from, replace_to):
    head, sep, body = text.partition("\n\n")
    return head + sep + body.replace(replace_from, replace_to)


def set_header(text, name, value):
    request = wire.from_wire(text)
    headers = {k: v for k, v in request["headers"].items()
               if k.lower() != name.lower()}
    headers[name] = value
    request["headers"] = headers
    return wire.to_wire(request)


def show(label, text):
    if VERBOSE:
        print(f"\n--- {label} ---\n{text}\n")


# --------------------------------------------------------------------------- #
# the attacks
# --------------------------------------------------------------------------- #
def t_modification(make):
    """Change the command inside a captured request."""
    target = make()
    captured = target.client_request("F")
    tampered = edit_body(captured, '"F"', '"B"')
    show("modification", tampered)
    accepted, command, _ = target.send(tampered)
    return not (accepted and command == "B")


def t_digest_forgery(make):
    """Change the command and attach a freshly computed digest."""
    target = make()
    captured = target.client_request("F")
    tampered = edit_body(captured, '"F"', '"B"')
    body = tampered.partition("\n\n")[2]
    for alg in ("sha256", "sha1", "md5"):
        attempt = set_header(tampered, "X-Digest-Alg", alg)
        attempt = set_header(attempt, "X-Digest", protocol.digest(alg, body))
        show(f"digest forgery {alg}", attempt)
        accepted, command, _ = target.send(attempt)
        if accepted and command == "B":
            return False
    return True


def t_mac_forgery(make):
    """Build a request from scratch, guessing at the authentication tag."""
    target = make()
    captured = target.client_request("F")
    request = wire.from_wire(captured)
    body = json.dumps({"command": "B"})
    guesses = ["", "0" * 64, "f" * 64,
               protocol.digest("hmac-sha256", body, b"secret")]
    for guess in guesses:
        attempt = wire.to_wire({**request, "body": body})
        attempt = set_header(attempt, "X-Digest", guess)
        show("mac forgery", attempt)
        accepted, command, _ = target.send(attempt)
        if accepted and command == "B":
            return False
    return True


def t_bit_flipping(make):
    """Change bytes of the body directly, without knowing any secret."""
    target = make()
    captured = target.client_request("F")
    request = wire.from_wire(captured)
    data = wire.json_body(request)

    hexed = "enc" in data
    original = None
    if hexed:
        try:
            original = bytearray(bytes.fromhex(str(data["enc"])))
        except ValueError:
            hexed = False          # not hex after all: flip the body text
    if original is None:
        original = bytearray(request["body"].encode("utf-8"))

    # "F" differs from "B", "L" and "R" by these bits
    deltas = [ord("F") ^ ord(other) for other in "BLR"]
    for position in range(len(original)):
        for delta in deltas:
            flipped = bytearray(original)
            flipped[position] ^= delta
            if hexed:
                body = json.dumps({"enc": bytes(flipped).hex()})
            else:
                try:
                    body = bytes(flipped).decode("utf-8")
                except UnicodeDecodeError:
                    continue
            attempt = wire.to_wire({**request, "body": body})
            accepted, command, _ = target.send(attempt)
            if accepted and command != "F":
                show("bit flipping", attempt)
                return False
    return True


def t_replay(make):
    """Send one captured request a second time, byte for byte."""
    target = make()
    captured = target.client_request("F")
    first, _, _ = target.send(captured)
    show("replay", captured)
    again, command, _ = target.send(captured)
    if not first:
        return False          # the honest request did not work at all
    return not again


def t_duplicate(make):
    """Hold a request back, let a later one through, then send the old one."""
    target = make()
    first = target.client_request("F")
    second = target.client_request("L")
    target.send(second)
    show("stale request", first)
    accepted, _, _ = target.send(first)
    return not accepted


def t_unauthenticated(make):
    """Invent a request that merely claims to be somebody."""
    target = make()
    for user in ("student",):
        attempt = wire.to_wire(wire.new_request(
            path="/car/command", headers={"X-User": user},
            body=json.dumps({"command": "F"})))
        show("unauthenticated", attempt)
        accepted, _, _ = target.send(attempt)
        if accepted:
            return False
    return True


def t_authorization(make):
    """Use the honest client to ask for an action no driver may perform."""
    target = make()
    for command, user in (("ADMIN_RESET", "student"),):
        attempt = target.client_request(command, user=user)
        show(f"authorization {user}:{command}", attempt)
        accepted, applied, _ = target.send(attempt)
        if accepted and applied == command:
            return False
    return True


def t_timing(make, rounds=7):
    """Compare how long two different guesses take."""
    target = make()
    student_module = getattr(target.proto, "module", None)
    code = getattr(student_module, "MAINTENANCE_CODE", protocol.MAINTENANCE_CODE)
    wrong = "".join("x" for _ in code)
    close = code[:-1] + "x"

    def measure(guess):
        samples = []
        for _ in range(rounds):
            _, ms = target.maintenance(guess)
            samples.append(ms)
        return statistics.median(samples)

    slow = measure(close)
    fast = measure(wrong)
    if VERBOSE:
        print(f"\n--- timing ---\nfirst-position guess {fast:.1f} ms   "
              f"near guess {slow:.1f} ms\n")
    return (slow - fast) < 5.0


# Each entry is (name, function, what the attacker did).  The description says
# only what was sent - never what would stop it.
TESTS = [
    ("Modification", t_modification,
     "Changes the command in a captured request before sending it."),
    ("Digest forgery", t_digest_forgery,
     "Changes a captured command and attaches a different digest."),
    ("Bit flipping", t_bit_flipping,
     "Changes individual bits in the request body."),
    ("Tag forgery", t_mac_forgery,
     "Builds a changed request and tries several tag values."),
    ("Replay", t_replay,
     "Sends the same captured request again without changing it."),
    ("Duplicate request", t_duplicate,
     "Sends a later request first, then sends an earlier one."),
    ("Authentication", t_unauthenticated,
     "Creates a request that claims to come from an account."),
    ("Authorization", t_authorization,
     "Asks for Workshop reset, which no driver account may do."),
    ("Timing behaviour", t_timing,
     "Sends two different maintenance codes to the door."),
]


def run_checks(scenario_id="student"):
    """Run every check and return a list of plain dictionaries.

    Each check gets its own Session, so it starts from empty client and server
    memory and, for the student scenario, a freshly loaded student file.  The
    live page session is never touched.
    """
    results = []
    for name, test, description in TESTS:
        def make():
            return Target(scenarios.Session(scenario_id).protocol)
        try:
            ok, error = bool(test(make)), ""
        except Exception as exc:
            ok, error = False, f"{type(exc).__name__}: {exc}"
        results.append({"name": name, "description": description,
                        "ok": ok, "error": error})
    return results


def run(scenario_id="student"):
    session = scenarios.Session(scenario_id)
    if session.error:
        print(f"could not load the protocol: {session.error}")
        return 2

    print(f"Target: {scenarios.BY_ID[scenario_id]['name']}\n")
    passed = 0
    for name, test, _description in TESTS:
        def make():
            fresh = scenarios.Session(scenario_id)
            return Target(fresh.protocol)
        try:
            ok = bool(test(make))
        except Exception as exc:
            print(f"{name:<22}ERROR  {type(exc).__name__}: {exc}")
            continue
        passed += ok
        print(f"{name:<22}{'PASS' if ok else 'FAIL'}")
    print(f"\n{passed}/{len(TESTS)} passed")
    return 0 if passed == len(TESTS) else 1


def main(argv):
    global VERBOSE
    scenario_id = "student"
    args = list(argv[1:])
    while args:
        arg = args.pop(0)
        if arg == "--scenario" and args:
            scenario_id = args.pop(0)
        elif arg in ("-v", "--verbose"):
            VERBOSE = True
        elif arg in ("-h", "--help"):
            print(__doc__)
            print("scenarios: " + ", ".join(scenarios.BY_ID))
            return 0
        else:
            print(f"unknown option {arg!r}  (try --help)")
            return 2
    if scenario_id not in scenarios.BY_ID:
        print(f"unknown scenario {scenario_id!r}: "
              + ", ".join(scenarios.BY_ID))
        return 2
    return run(scenario_id)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
