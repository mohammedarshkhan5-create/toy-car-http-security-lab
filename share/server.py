#!/usr/bin/env python3
"""
Toy-Car HTTP Interceptor - a small cyber-security teaching project.

Three parties share one browser page:

    Client        presses a button, which becomes an HTTP request
    Interceptor   sits in the middle: hold, edit, drop, delay, replay
    Car server    checks the request and moves the car, or refuses

One button press travels like this:

    Client panel                                        Car server
    (browser)                                           (deliver, below)
        |                                                     ^
        |  POST /client/press {"command": "F"}                |
        v                                                     |
    create_request()  ->  raw HTTP text  ->  Interceptor  ->  verify_request()
    (the protocol)        (wire.py)          (hold, edit,     authorize()
                                              drop, delay,    move the car
                                              replay)

Run it:

    python3 server.py
    python3 server.py --scenario access   start on a particular scenario
    python3 server.py --host 0.0.0.0 --port 8080

Then open http://localhost:8000

Files:
    server.py            this file - HTTP transport and wiring only
    carsim.py            the car
    wire.py              request <-> raw HTTP text
    protocol.py          the built-in protocol
    labusers.py          the account and its password
    scenarios.py         the scenario table
    interceptor.py       the attacker's queue and log
    student_solution.py  THE FILE STUDENTS EDIT
    attack_tests.py      python3 attack_tests.py

Standard library only.  student_solution.py is the only file meant to be
edited; you do not need to edit this one.
"""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import attack_tests
import carsim
import interceptor as interceptor_mod
import labusers
import protocol
import scenarios
import ui
import wire

HOST = "localhost"
PORT = 8000

session = scenarios.Session()
mitm = interceptor_mod.Interceptor()


# --------------------------------------------------------------------------- #
# The car server: what happens when a request finally arrives
# --------------------------------------------------------------------------- #
def deliver(text):
    """Hand one raw request to the car server. Returns a result dict.

    In order:  read the text  ->  which door was knocked on  ->  is the
    request believable  ->  is this user allowed to do that  ->  move the car.
    """
    request = wire.from_wire(text)
    if request is None:
        return {"code": 400, "status": "malformed"}

    path = urlparse(request.get("path", "")).path
    proto = session.protocol

    if path == "/maintenance/auth":
        try:
            result = proto.maintenance_auth(request, session.server_state)
        except Exception as exc:
            return {"code": 500, "status": "error", "reason": repr(exc)}
        ok = bool(result.get("ok"))
        return {"code": 200 if ok else 403,
                "status": "accepted" if ok else "rejected"}

    if path != "/car/command":
        return {"code": 404, "status": "no such endpoint"}

    try:
        checked = proto.verify_request(request, session.server_state)
    except Exception as exc:
        return {"code": 500, "status": "error", "reason": repr(exc)}
    if not isinstance(checked, dict) or not checked.get("ok"):
        reason = (checked or {}).get("reason", "") if isinstance(checked, dict) else ""
        return {"code": 403, "status": "rejected", "reason": reason}

    user = str(checked.get("user", ""))
    command = str(checked.get("command", "")).upper()
    action = carsim.ACTION_OF.get(command)
    if action is None:
        return {"code": 400, "status": "rejected", "reason": "unknown command"}

    try:
        allowed = proto.authorize(user, action, session.server_state)
    except Exception as exc:
        return {"code": 500, "status": "error", "reason": repr(exc)}
    if not allowed:
        carsim.note(command, "refused")
        return {"code": 403, "status": "rejected",
                "reason": f"{user!r} may not {action}"}

    carsim.apply_command(command)
    carsim.note(command, "accepted")
    return {"code": 200, "status": "accepted", "command": command,
            "user": user}


# The security checks run in a worker thread: a full pass includes real waits,
# so the browser gets a job to poll instead of a request that hangs.
CHECKS = {"state": "idle", "results": [], "passed": 0, "total": 0}
CHECKS_LOCK = threading.Lock()


def _run_checks():
    try:
        results = attack_tests.run_checks("student")
    except Exception as exc:
        with CHECKS_LOCK:
            CHECKS.update(state="error", results=[], passed=0, total=0,
                          error=f"{type(exc).__name__}: {exc}")
        return
    with CHECKS_LOCK:
        CHECKS.update(state="done", results=results, error="",
                      passed=sum(1 for r in results if r["ok"]),
                      total=len(results))


def student_view(result):
    """What the page is allowed to show.

    A built-in scenario only ever says "rejected": the reason would explain the
    mechanism the class is meant to find.  In the Student Solution scenario
    the reason is the student's own note from their verify_request, so it is
    shown back to help them debug.
    """
    out = {k: v for k, v in result.items() if k != "reason"}
    if session.scenario_id == "student" and result.get("reason"):
        out["reason"] = result["reason"]
    return out


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass                      # keep the console clean

    # -- helpers ------------------------------------------------------------ #
    def _send(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, ctype="text/plain; charset=utf-8", status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    # -- routing ------------------------------------------------------------ #
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send_text(ui.PAGE, "text/html; charset=utf-8")
        elif path == "/car/state":
            self._send(carsim.state())
        elif path == "/scenario/state":
            info = session.info()
            info["commands"] = carsim.ACTION_OF
            self._send(info)
        elif path == "/checks/state":
            with CHECKS_LOCK:
                self._send(dict(CHECKS))
        elif path == "/intercept/state":
            self._send({"on": mitm.on, "pending": mitm.pending_list(),
                        "captures": mitm.capture_list()})
        elif path == "/history":
            self._send({"history": [student_view(h)
                                    for h in mitm.history_list()]})
        elif path == "/hashes":
            self._send_text(labusers.hash_export())
        elif path == "/favicon.ico":
            self.send_response(204)      # browsers ask; there is none to give
            self.end_headers()
        else:
            self._send({"error": "not found"}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        route = {
            "/client/press": self._press,
            "/client/maintenance": self._maintenance,
            "/scenario/select": self._select,
            "/scenario/reset": self._reset,
            "/scenario/option": self._option,
            "/intercept/toggle": self._toggle,
            "/intercept/action": self._action,
            "/wire/send": self._wire_send,
            "/tools/digest": self._digest,
            "/car/reset": self._car_reset,
            "/checks/run": self._checks_run,
        }.get(path)
        if route is None:
            self._send({"error": "not found"}, status=404)
            return
        route()

    # -- client ------------------------------------------------------------- #
    def _press(self):
        """A button press in the Client panel."""
        data = self._read_json()
        command = str(data.get("command", "")).upper()
        user = str(data.get("user", "student"))
        if command not in carsim.COMMANDS:
            self._send({"error": "unknown command"}, status=400)
            return

        session.client_state["password"] = str(data.get("password", ""))
        session.client_state["user"] = user
        try:
            request = session.protocol.create_request(
                command, user, session.client_state)
        except Exception as exc:
            self._send(student_view({"status": "error", "code": 500,
                                     "reason": repr(exc)}), status=200)
            return
        if not isinstance(request, dict):
            self._send({"status": "error", "code": 500}, status=200)
            return

        result = mitm.send(wire.to_wire(request), deliver, source="client")
        view = student_view(result)
        # A password hint for the honest Client panel only.  The reason string
        # is read here on the server and never sent; the browser gets only a
        # coarse missing/wrong flag, and only in scenarios that ask for a
        # password.  Crafted requests (/wire/send) and the Network log are
        # untouched, so an attacker still learns nothing from a refusal.
        if (getattr(session.protocol, "require_auth", False)
                and result.get("status") == "rejected"):
            reason = str(result.get("reason", "")).lower()
            if not session.client_state.get("password", ""):
                view["auth"] = "missing"
            elif "password" in reason or "account" in reason:
                view["auth"] = "wrong"
        self._send(view)

    def _maintenance(self):
        """The maintenance code box in the Client panel."""
        code = str(self._read_json().get("code", ""))
        request = wire.new_request(path="/maintenance/auth",
                                   body=json.dumps({"code": code}))
        result = mitm.send(wire.to_wire(request), deliver, source="client")
        self._send(student_view(result))

    def _checks_run(self):
        """Start a check run against the student file, if one is not going."""
        if session.scenario_id != "student":
            self._send({"error": "not the student scenario"}, status=400)
            return
        with CHECKS_LOCK:
            if CHECKS["state"] == "running":
                self._send(dict(CHECKS))
                return
            CHECKS.update(state="running", results=[], passed=0, total=0,
                          error="")
            snapshot = dict(CHECKS)
        threading.Thread(target=_run_checks, daemon=True).start()
        self._send(snapshot)

    # -- scenario ----------------------------------------------------------- #
    def _select(self):
        wanted = str(self._read_json().get("id", ""))
        if not session.select(wanted):
            self._send({"error": "unknown scenario"}, status=400)
            return
        mitm.clear()
        if not session.has_interceptor:
            mitm.set_on(False)      # nothing on the page could release a held request
        self._send(session.info())

    def _reset(self):
        session.reset()
        mitm.clear()
        if not session.has_interceptor:
            mitm.set_on(False)
        self._send(session.info())

    def _option(self):
        data = self._read_json()
        session.set_option(str(data.get("name", "")), bool(data.get("value")))
        self._send(session.info())

    def _car_reset(self):
        carsim.reset()
        self._send({"ok": True})

    # -- interceptor -------------------------------------------------------- #
    def _toggle(self):
        if not session.has_interceptor:
            self._send({"on": False, "error": "no interceptor in this scenario"},
                       status=400)
            return
        self._send({"on": mitm.toggle()})

    def _action(self):
        data = self._read_json()
        try:
            req_id = int(data.get("id"))
        except (TypeError, ValueError):
            self._send({"error": "bad id"}, status=400)
            return
        ok = mitm.action(req_id, str(data.get("action", "forward")),
                         raw=data.get("raw"), delay_ms=data.get("delay_ms", 0))
        self._send({"ok": ok}, status=200 if ok else 404)

    def _wire_send(self):
        """Send hand-written request text straight at the car server."""
        raw = str(self._read_json().get("raw", ""))
        result = mitm.send(raw, deliver, source="replay")
        self._send(student_view(result))

    def _digest(self):
        """Digest calculator for the Attacker tools.  Plain digests only: it
        has no secret to offer, so it offers no algorithm that needs one."""
        data = self._read_json()
        alg = str(data.get("alg", "sha256")).lower()
        text = str(data.get("text", ""))
        if alg not in protocol.PLAIN_ALGS:
            self._send({"error": f"unknown algorithm {alg}"}, status=400)
            return
        self._send({"digest": protocol.digest(alg, text)})


# --------------------------------------------------------------------------- #
def main(argv):
    global HOST, PORT
    args = list(argv[1:])
    while args:
        arg = args.pop(0)
        if arg == "--scenario" and args:
            session.select(args.pop(0))
        elif arg == "--host" and args:
            HOST = args.pop(0)
        elif arg == "--port" and args:
            PORT = int(args.pop(0))
        elif arg in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            print(f"unknown option {arg!r}  (try --help)")
            return 2

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    wire.HOST = f"{HOST}:{PORT}"
    print(f"Toy-Car HTTP Interceptor running at {url}")
    print(f"Scenario: {session.info()['name']}")
    print("Open that URL in your browser.  Ctrl+C to stop.")
    try:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
