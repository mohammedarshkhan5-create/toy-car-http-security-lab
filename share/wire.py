"""Network format helpers: a request as text, and text back to a request.

A "request" in this project is a plain dictionary:

    {
        "method":  "POST",
        "path":    "/car/command",
        "headers": {"X-User": "student", ...},   # upper/lower case in names does not matter
        "body":    '{"command": "F"}',            # always a string
    }

`to_wire()` turns that dictionary into the text an HTTP request is made of
as it crosses the network.  `from_wire()` turns such text back into the
dictionary.

The interceptor only ever handles the text form.  The client and the car
server work with the dictionary form.


You do not need to edit this file.
"""

import json

CRLF = "\n"

# Shown in the Host line of every request.  server.py sets it to match the port
# it is actually listening on, so the text students read is the real address.
HOST = "localhost:8000"


def new_request(method="POST", path="/car/command", headers=None, body=""):
    """Build a request dictionary with sensible defaults."""
    return {
        "method": method,
        "path": path,
        "headers": dict(headers or {}),
        "body": body if isinstance(body, str) else json.dumps(body),
    }


def to_wire(request):
    """Request dictionary -> raw HTTP text."""
    method = request.get("method", "POST")
    path = request.get("path", "/car/command")
    body = request.get("body", "")
    if not isinstance(body, str):
        body = json.dumps(body)
    lines = [f"{method} {path} HTTP/1.1", f"Host: {HOST}"]
    lines.append("Content-Type: application/json")
    for key, value in (request.get("headers") or {}).items():
        if key.lower() in ("host", "content-type", "content-length"):
            continue
        lines.append(f"{key}: {value}")
    lines.append(f"Content-Length: {len(body.encode('utf-8'))}")
    lines.append("")
    lines.append(body)
    return CRLF.join(lines)


def from_wire(text):
    """Raw HTTP text -> request dictionary, or None if it cannot be parsed."""
    if not isinstance(text, str) or not text.strip():
        return None
    head, _, body = text.replace("\r\n", "\n").partition("\n\n")
    lines = [line for line in head.split("\n") if line.strip()]
    if not lines:
        return None
    parts = lines[0].split()
    if len(parts) < 2:
        return None
    method, path = parts[0].upper(), parts[1]
    headers = {}
    for line in lines[1:]:
        key, sep, value = line.partition(":")
        if sep:
            headers[key.strip()] = value.strip()
    return {"method": method, "path": path, "headers": headers, "body": body}


def header(request, name, default=""):
    """Read one header from a request, ignoring upper/lower case."""
    wanted = name.lower()
    for key, value in (request.get("headers") or {}).items():
        if key.lower() == wanted:
            return value
    return default


def json_body(request):
    """The request body decoded as JSON, or {} if it is not valid JSON."""
    try:
        data = json.loads(request.get("body") or "{}")
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def body_preview(request, limit=60):
    """A short one-line view of the body, for the monitor log."""
    body = (request.get("body") or "").replace("\n", " ").strip()
    return body[:limit] + ("…" if len(body) > limit else "")
