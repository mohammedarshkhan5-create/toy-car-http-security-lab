"""The party in the middle.

Everything here works on the raw text of a request.  This module deliberately
does not import the protocol, the accounts or the secrets: the only thing it ever
sees is what actually crossed the network, plus how long the far end took to
answer.


You do not need to edit this file.
"""

import threading
import time

HOLD_TIMEOUT = 120.0     # seconds a held request waits before giving up
MAX_HISTORY = 300
MAX_CAPTURES = 40


def _now():
    return time.strftime("%H:%M:%S")


class Interceptor:
    def __init__(self):
        self.lock = threading.Lock()
        self.on = False
        self.pending = {}
        self.history = []
        self.captures = []
        self._next_id = 0

    # -- switches ----------------------------------------------------------- #
    def toggle(self):
        with self.lock:
            self.on = not self.on
            return self.on

    def set_on(self, on):
        with self.lock:
            self.on = bool(on)

    def clear(self):
        with self.lock:
            self.history.clear()
            self.captures.clear()
            for info in self.pending.values():
                info["action"] = "drop"
                info["event"].set()
            self.pending.clear()

    # -- log ---------------------------------------------------------------- #
    def log(self, source, text, result, flags=()):
        record = {
            "ts": _now(),
            "source": source,
            "status": result.get("status", ""),
            "code": result.get("code", 0),
            "ms": round(float(result.get("ms", 0.0)), 1),
            "reason": result.get("reason", ""),
            "flags": list(flags),
            "raw": text,
        }
        with self.lock:
            self.history.append(record)
            if len(self.history) > MAX_HISTORY:
                del self.history[:len(self.history) - MAX_HISTORY]

    def capture(self, text):
        line = text.split("\n", 1)[0]
        with self.lock:
            self.captures.append({"ts": _now(), "line": line, "raw": text})
            if len(self.captures) > MAX_CAPTURES:
                del self.captures[:len(self.captures) - MAX_CAPTURES]

    # -- the network -------------------------------------------------------- #
    def send(self, text, deliver, source="client"):
        """Put one request on the network.

        `deliver(text)` is the far end.  It returns a result dict; this method
        adds the round-trip time in milliseconds.
        """
        self.capture(text)
        if source != "client" or not self.on:
            return self._deliver(text, deliver, source)

        with self.lock:
            self._next_id += 1
            req_id = self._next_id
            event = threading.Event()
            self.pending[req_id] = {"id": req_id, "ts": _now(), "raw": text,
                                    "event": event, "action": None,
                                    "edited": text, "delay": 0.0}

        fired = event.wait(HOLD_TIMEOUT)
        with self.lock:
            info = self.pending.pop(req_id, None)

        if not fired or info is None or info["action"] is None:
            result = {"code": 0, "status": "timeout"}
            self.log("client", text, result, flags=["held"])
            return result
        if info["action"] == "drop":
            result = {"code": 0, "status": "dropped"}
            self.log("client", text, result, flags=["held"])
            return result

        if info["delay"]:
            time.sleep(info["delay"])
        flags = ["held"]
        if info["edited"].strip() != text.strip():
            flags.append("edited")
        if info["delay"]:
            flags.append("delayed")
        return self._deliver(info["edited"], deliver, "intercept", flags)

    def _deliver(self, text, deliver, source, flags=()):
        started = time.perf_counter()
        result = deliver(text)
        result["ms"] = (time.perf_counter() - started) * 1000.0
        self.log(source, text, result, flags=flags)
        return result

    # -- acting on a held request ------------------------------------------- #
    def action(self, req_id, action, raw=None, delay_ms=0):
        with self.lock:
            info = self.pending.get(req_id)
            if info is None:
                return False
            info["action"] = "drop" if action == "drop" else "forward"
            if raw is not None:
                info["edited"] = str(raw)
            try:
                info["delay"] = max(0.0, float(delay_ms)) / 1000.0
            except (TypeError, ValueError):
                info["delay"] = 0.0
            info["event"].set()
        return True

    # -- views for the panel ------------------------------------------------ #
    def pending_list(self):
        with self.lock:
            return [{"id": i["id"], "ts": i["ts"], "raw": i["raw"]}
                    for i in self.pending.values()]

    def history_list(self):
        with self.lock:
            return list(self.history)

    def capture_list(self):
        with self.lock:
            return list(reversed(self.captures))
