"""mcp_bridge.py — zero-dependency stdio MCP server for the official Blender Lab MCP add-on (Blender 5.1+).

Translates standard MCP JSON-RPC 2.0 stdio messages (Antigravity, Claude Code, Codex, Claude Desktop)
into the official Blender Lab add-on's null-byte-delimited TCP JSON wire protocol on 127.0.0.1:9876.

Zero third-party packages required (Python 3.10+ standard library only; no uv/uvx needed).

Quick connection test:
  python -X utf8 scripts/blender/mcp_bridge.py --check

MCP client config (Antigravity ~/.gemini/config/mcp_config.json):
  {
    "mcpServers": {
      "blender": {
        "command": "python",
        "args": ["-X", "utf8", "<skill>/scripts/blender/mcp_bridge.py"]
      }
    }
  }
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from typing import Any

HOST = os.environ.get("BLENDER_HOST", "127.0.0.1")
PORT = int(os.environ.get("BLENDER_PORT", "9876"))
TIMEOUT = float(os.environ.get("BLENDER_MCP_TIMEOUT", "60"))

SERVER_INFO = {"name": "chiaki-blender-mcp-bridge", "version": "1.0.0"}
PROTOCOL_VERSION = "2025-03-26"

TOOLS = [
    {
        "name": "blender_get_scene_info",
        "description": "Inspect the currently open Blender scene: Blender version, render engine, resolution, fps, active camera, lights, and object summary.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "blender_execute_python",
        "description": "Execute Python (bpy) code inside the open Blender GUI session for interactive look-dev (staging, lighting, materials, camera checks). Assign output data to the `result` dict or print to stdout. Do NOT use for batch frame rendering — run final batches headless via scripts/run_queue.py blender.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code using bpy to run in Blender's main thread."},
                "strict_json": {"type": "boolean", "default": False, "description": "Require strict JSON types in `result` dict (default false falls back to repr)."},
            },
            "required": ["code"],
        },
    },
    {
        "name": "blender_get_camera",
        "description": "Read the active camera's exact world location, XYZ Euler rotation (radians & degrees), focal length (mm), sensor width, and DOF settings so manual GUI camera tweaks can be saved back into shot.py.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "blender_set_camera",
        "description": "Position and aim the active camera interactively in the open Blender scene.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3, "description": "[x, y, z] world location in metres"},
                "look_at": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3, "description": "Optional [x, y, z] target point to aim camera toward"},
                "rotation_deg": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3, "description": "Optional [rx, ry, rz] XYZ Euler rotation in degrees (ignored if look_at is set)"},
                "lens_mm": {"type": "number", "description": "Optional focal length in mm"},
                "dof_fstop": {"type": "number", "description": "Optional aperture f-stop (enables DOF when > 0)"},
            },
        },
    },
    {
        "name": "blender_render_preview",
        "description": "Render ONE look-dev still image from the active camera to `out_path` (PNG) so you can inspect lighting, framing, and materials visually.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "out_path": {"type": "string", "description": "Absolute output PNG file path (parent directories created automatically)."},
                "width": {"type": "integer", "default": 960, "description": "Preview width in pixels (default 960)."},
                "height": {"type": "integer", "default": 540, "description": "Preview height in pixels (default 540)."},
                "samples": {"type": "integer", "default": 16, "description": "Render samples for quick look-dev still (default 16)."},
            },
            "required": ["out_path"],
        },
    },
]


def send_blender(code: str, strict_json: bool = False, host: str = HOST, port: int = PORT, timeout: float = TIMEOUT) -> dict[str, Any]:
    payload = json.dumps({"type": "execute", "strict_json": bool(strict_json), "code": code}).encode("utf-8") + b"\x00"
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(payload)
            chunks = []
            while True:
                data = sock.recv(65536)
                if not data:
                    break
                chunks.append(data)
                if b"\x00" in data:
                    break
    except OSError as e:
        return {
            "status": "error",
            "message": (
                f"Cannot connect to Blender MCP socket at {host}:{port} ({e}). "
                "Make sure Blender 5.1+ is open, the official Blender Lab MCP add-on is enabled "
                "(Edit -> Preferences -> Add-ons -> MCP), and 'Start MCP Server' is running."
            ),
        }
    raw = b"".join(chunks).split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
    if not raw:
        return {"status": "error", "message": "Empty response from Blender MCP socket."}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON from Blender: {e}", "raw": raw[:500]}


def call_tool(name: str, args: dict[str, Any], host: str, port: int) -> dict[str, Any]:
    if name == "blender_get_scene_info":
        code = """
import bpy
sc = bpy.context.scene
cam = sc.camera
objs = []
for o in sc.objects[:120]:
    objs.append({
        "name": o.name,
        "type": o.type,
        "location": [round(v, 4) for v in o.location],
        "visible": not o.hide_viewport,
    })
result = {
    "blender_version": bpy.app.version_string,
    "filepath": bpy.data.filepath or "(unsaved)",
    "scene": sc.name,
    "engine": sc.render.engine,
    "resolution": [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
    "fps": sc.render.fps,
    "frame_current": sc.frame_current,
    "active_camera": cam.name if cam else None,
    "object_count": len(sc.objects),
    "objects": objs,
}
""".strip()
        return send_blender(code, strict_json=True, host=host, port=port)

    if name == "blender_execute_python":
        code = str(args.get("code") or "")
        strict = bool(args.get("strict_json", False))
        return send_blender(code, strict_json=strict, host=host, port=port)

    if name == "blender_get_camera":
        code = """
import bpy, math
sc = bpy.context.scene
cam = sc.camera
if cam is None:
    result = {"error": "No active scene camera."}
else:
    e = cam.matrix_world.to_euler("XYZ")
    cd = cam.data
    result = {
        "name": cam.name,
        "location": [round(v, 5) for v in cam.matrix_world.translation],
        "rotation_rad": [round(v, 5) for v in e],
        "rotation_deg": [round(math.degrees(v), 3) for v in e],
        "lens_mm": round(cd.lens, 3),
        "sensor_width_mm": round(cd.sensor_width, 3),
        "clip_start": cd.clip_start,
        "clip_end": cd.clip_end,
        "dof_enabled": cd.dof.use_dof,
        "dof_focus_distance": round(cd.dof.focus_distance, 4),
        "dof_fstop": round(cd.dof.aperture_fstop, 3),
    }
""".strip()
        return send_blender(code, strict_json=True, host=host, port=port)

    if name == "blender_set_camera":
        code = f"""
import bpy, math
from mathutils import Vector
sc = bpy.context.scene
cam = sc.camera
if cam is None:
    raise RuntimeError("No active scene camera.")
cam.rotation_mode = "XYZ"
loc = {json.dumps(args.get("location"))}
look_at = {json.dumps(args.get("look_at"))}
rot_deg = {json.dumps(args.get("rotation_deg"))}
lens_mm = {json.dumps(args.get("lens_mm"))}
dof_fstop = {json.dumps(args.get("dof_fstop"))}
if loc is not None:
    cam.location = tuple(float(v) for v in loc)
if look_at is not None:
    direction = Vector(tuple(float(v) for v in look_at)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler("XYZ")
elif rot_deg is not None:
    cam.rotation_euler = tuple(math.radians(float(v)) for v in rot_deg)
if lens_mm is not None:
    cam.data.lens = float(lens_mm)
if dof_fstop is not None and float(dof_fstop) > 0:
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = float(dof_fstop)
    if look_at is not None:
        cam.data.dof.focus_distance = (Vector(tuple(float(v) for v in look_at)) - cam.location).length
bpy.context.view_layer.update()
e = cam.rotation_euler
result = {{
    "name": cam.name,
    "location": [round(v, 5) for v in cam.location],
    "rotation_deg": [round(math.degrees(v), 3) for v in e],
    "lens_mm": round(cam.data.lens, 3),
}}
""".strip()
        return send_blender(code, strict_json=True, host=host, port=port)

    if name == "blender_render_preview":
        out_path = str(args.get("out_path") or "").replace("\\", "/")
        width = int(args.get("width") or 960)
        height = int(args.get("height") or 540)
        samples = int(args.get("samples") or 16)
        code = f"""
import bpy, os
sc = bpy.context.scene
out_p = {json.dumps(out_path)}
os.makedirs(os.path.dirname(os.path.abspath(out_p)), exist_ok=True)
old = (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.render.filepath, sc.render.image_settings.file_format)
old_samples = getattr(sc.cycles, "samples", None) if sc.render.engine == "CYCLES" else getattr(sc.eevee, "taa_render_samples", None)
try:
    sc.render.resolution_x = {width}
    sc.render.resolution_y = {height}
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_p
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = {samples}
    else:
        try: sc.eevee.taa_render_samples = {samples}
        except Exception: pass
    bpy.ops.render.render(write_still=True)
finally:
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.render.filepath, sc.render.image_settings.file_format = old
    if old_samples is not None:
        if sc.render.engine == "CYCLES": sc.cycles.samples = old_samples
        else:
            try: sc.eevee.taa_render_samples = old_samples
            except Exception: pass
result = {{"rendered": out_p, "exists": os.path.exists(out_p), "bytes": os.path.getsize(out_p) if os.path.exists(out_p) else 0}}
""".strip()
        return send_blender(code, strict_json=True, host=host, port=port)

    return {"status": "error", "message": f"Unknown tool: {name}"}


def write_msg(obj: dict[str, Any]):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def serve(host: str, port: int) -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        # Notifications have no id -> no response required
        if req_id is None:
            continue

        if method == "initialize":
            client_ver = params.get("protocolVersion") or PROTOCOL_VERSION
            write_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": client_ver,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            })
        elif method == "ping":
            write_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif method == "tools/list":
            write_msg({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            tname = params.get("name", "")
            targs = params.get("arguments") or {}
            res = call_tool(tname, targs, host, port)
            is_err = res.get("status") == "error"
            write_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}],
                    "isError": is_err,
                },
            })
        else:
            write_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Zero-dependency stdio MCP bridge for official Blender Lab MCP add-on")
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--check", action="store_true", help="Test live connection to Blender MCP socket and print scene JSON")
    a = ap.parse_args()
    if a.check:
        res = call_tool("blender_get_scene_info", {}, a.host, a.port)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("status") == "ok" else 1
    return serve(a.host, a.port)


if __name__ == "__main__":
    sys.exit(main())
