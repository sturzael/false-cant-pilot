#!/usr/bin/env python3
"""Fake MCP tool server for the false-"I can't" pilot.

Speaks MCP (JSON-RPC 2.0, newline-delimited) over stdio. Exposes a tool set for one
(task, condition), logs every call to FCP_LOG as JSON lines, and touches nothing real.

Env: FCP_TASKS (path to tasks.json), FCP_TASK (e.g. T01), FCP_COND (C0|C1|C2|C3|X), FCP_LOG.
"""
import json
import os
import re
import sys

TASKS = json.load(open(os.environ["FCP_TASKS"]))
TASK = next(t for t in TASKS["tasks"] if t["id"] == os.environ["FCP_TASK"])
COND = os.environ["FCP_COND"]
LOG = os.environ["FCP_LOG"]

STOP = {"the", "and", "for", "with", "this", "that", "from", "into", "your", "you", "can", "tool",
        "tools", "use", "set", "get", "list", "create", "existing", "message", "messages"}


def schema(params):
    props = {k: {"type": v} for k, v in params.items()}
    return {"type": "object", "properties": props}


def tool(t):
    return {"name": t["name"], "description": t["description"], "inputSchema": schema(t["params"])}


SEARCH = {"name": "SEARCH_TOOLS",
          "description": "Search the full catalogue of available app tools by describing what you want to do. "
                         "Returns matching tools with their names, descriptions and parameters. "
                         "Call them with EXECUTE_TOOL.",
          "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
EXECUTE = {"name": "EXECUTE_TOOL",
           "description": "Execute any catalogue tool by name with a JSON object of arguments.",
           "inputSchema": {"type": "object", "properties": {"tool_name": {"type": "string"},
                                                             "arguments": {"type": "object"}},
                           "required": ["tool_name"]}}

target, sibling = TASK["target"], TASK["sibling"]
distractors = TASKS["distractors"]

# What is listed directly, and what the searchable catalogue holds.
if COND in ("C0", "X"):
    listed = [tool(d) for d in distractors] + [tool(target)]
    catalogue = []
elif COND in ("C1", "C3"):
    listed = [tool(d) for d in distractors] + [SEARCH, EXECUTE]
    catalogue = [target, sibling] + distractors
elif COND == "C2":
    listed = [tool(d) for d in distractors] + [tool(sibling), SEARCH, EXECUTE]
    catalogue = [target, sibling] + distractors
else:
    raise SystemExit(f"unknown condition {COND}")

KNOWN = {t["name"]: t for t in [target, sibling] + distractors}


def log(entry):
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def words(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if len(w) >= 4 and w not in STOP}


def search(query):
    q = words(query)
    scored = []
    for t in catalogue:
        overlap = len(q & words(t["name"].replace("_", " ") + " " + t["description"]))
        if overlap:
            scored.append((overlap, t["name"], t))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"name": t["name"], "description": t["description"], "parameters": t["params"]}
            for _, _, t in scored[:5]]


def run_named(name, args):
    """Result for calling a catalogue/listed tool by name. Returns (text, is_error, kind)."""
    if name == target["name"]:
        if COND == "X":
            # The tool works, but it cannot do the impossible request; it just does its normal job.
            return json.dumps({"ok": True, "note": "Operation completed for the given arguments."}), False, "target"
        return json.dumps({"ok": True, "result": f"{name} succeeded", "arguments": args}), False, "target"
    if name == sibling["name"]:
        return sibling["error"], True, "sibling"
    if name in KNOWN:
        return json.dumps({"ok": True, "result": f"{name}: no relevant data"}), False, "distractor"
    return f"Error: unknown tool '{name}'.", True, "unknown"


def call(name, args):
    if name == "SEARCH_TOOLS":
        res = search(str(args.get("query", "")))
        log({"tool": name, "args": args, "kind": "search", "returned": [r["name"] for r in res]})
        return json.dumps({"results": res}), False
    if name == "EXECUTE_TOOL":
        inner = str(args.get("tool_name", ""))
        inner_args = args.get("arguments") or {}
        if inner not in {t["name"] for t in catalogue} and inner not in {t["name"] for t in [target] + distractors if COND in ("C0", "X")}:
            text, err, kind = f"Error: unknown tool '{inner}'.", True, "unknown"
        else:
            text, err, kind = run_named(inner, inner_args)
        log({"tool": name, "inner": inner, "args": inner_args, "kind": kind, "error": err})
        return text, err
    text, err, kind = run_named(name, args)
    log({"tool": name, "args": args, "kind": kind, "error": err})
    return text, err


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    method, msg_id = msg.get("method"), msg.get("id")
    if msg_id is None:
        continue  # notification
    if method == "initialize":
        reply(msg_id, {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
                       "capabilities": {"tools": {}},
                       "serverInfo": {"name": "apps", "version": "1.0"}})
    elif method == "tools/list":
        reply(msg_id, {"tools": listed})
    elif method == "tools/call":
        p = msg.get("params", {})
        text, err = call(p.get("name", ""), p.get("arguments") or {})
        reply(msg_id, {"content": [{"type": "text", "text": text}], "isError": err})
    elif method == "ping":
        reply(msg_id, {})
    else:
        reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})
