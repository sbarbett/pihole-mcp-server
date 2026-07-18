"""
Unbound recursive-resolver control tools.

Manages the Unbound resolver(s) that sit *behind* Pi-hole, via Unbound's native
remote-control interface (the `unbound-control` TLS protocol implemented in pure
Python — no external binary, no SSH). Complements the Pi-hole tools: Pi-hole
owns blocking / adlists / upstream selection, while Unbound is the recursive
resolver doing the actual lookups — so cache flushes, resolver stats, and
resolver-level local data live here.

## Enabling remote control on Unbound

Unbound listens on a local UNIX socket by default; expose the control interface
over TLS/TCP so this server can reach it. In `unbound.conf`:

    remote-control:
        control-enable: yes
        control-interface: 127.0.0.1        # keep one local interface for unbound-control
        control-interface: 0.0.0.0          # or a specific LAN IP this MCP server can reach
        control-port: 8953
        control-use-cert: yes

IMPORTANT: do NOT keep a UNIX-socket control-interface (a path such as
`/run/unbound.ctl`) alongside the TCP interface. When *any* control-interface is
a UNIX socket, Unbound runs the entire control facility WITHOUT TLS
(`unbound-control status` shows `control(namedpipe)`), so the TCP port answers
in plaintext and TLS handshakes are refused. Use IP-address interfaces only —
add `127.0.0.1` so local `unbound-control` keeps working — and then
`unbound-control status` reports `control(ssl)`.

Generate the control certificates once with `unbound-control-setup` (creates
`unbound_server.pem`, `unbound_control.pem`, `unbound_control.key` in Unbound's
directory) and restart Unbound. Copy those three files to wherever this MCP
server runs and point the env vars below at them.

## Configuration (env / .env)

Primary resolver — set `UNBOUND_HOST` to enable the Unbound tools:

    UNBOUND_HOST           resolver host/IP exposing the control interface
    UNBOUND_PORT           control port (default 8953)
    UNBOUND_NAME           display name (default: the host)
    UNBOUND_CONTROL_CERT   client cert  -> unbound_control.pem
    UNBOUND_CONTROL_KEY    client key   -> unbound_control.key
    UNBOUND_SERVER_CERT    server cert  -> unbound_server.pem (used to verify)

Additional resolvers (optional, up to 4 total): `UNBOUND2_*`, `UNBOUND3_*`,
`UNBOUND4_*` with the same fields. A resolver that omits its cert paths falls
back to the primary's — convenient when every resolver shares one cert set.

Write operations (flush / local_data) fan out to every configured resolver,
because Unbound cache and runtime state is per-resolver.
"""

import os
import socket
import ssl
from typing import List, Dict, Optional, Any


def _instances() -> List[Dict[str, Any]]:
    """Read resolver instances from the environment (primary + UNBOUND2..4)."""
    out: List[Dict[str, Any]] = []
    for i in ("", "2", "3", "4"):
        host = os.getenv(f"UNBOUND{i}_HOST")
        if not host:
            continue
        out.append({
            "name": os.getenv(f"UNBOUND{i}_NAME", host),
            "host": host,
            "port": int(os.getenv(f"UNBOUND{i}_PORT", "8953")),
            "cert": os.getenv(f"UNBOUND{i}_CONTROL_CERT") or os.getenv("UNBOUND_CONTROL_CERT"),
            "key": os.getenv(f"UNBOUND{i}_CONTROL_KEY") or os.getenv("UNBOUND_CONTROL_KEY"),
            "ca": os.getenv(f"UNBOUND{i}_SERVER_CERT") or os.getenv("UNBOUND_SERVER_CERT"),
        })
    return out


def _send(inst: Dict[str, Any], command: str) -> str:
    """Speak the unbound-control protocol: mutual-TLS, send `UBCT1 <cmd>`, read reply."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False  # Unbound's server cert CN is "unbound", not the host
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=inst["ca"])
    ctx.load_cert_chain(certfile=inst["cert"], keyfile=inst["key"])
    with socket.create_connection((inst["host"], inst["port"]), timeout=10) as raw:
        raw.settimeout(10)
        with ctx.wrap_socket(raw) as sock:  # no SNI: Unbound's server cert CN is "unbound"
            sock.sendall(f"UBCT1 {command}\n".encode())
            chunks: List[bytes] = []
            while True:
                b = sock.recv(65536)
                if not b:
                    break
                chunks.append(b)
    return b"".join(chunks).decode("utf-8", "replace").strip()


def _fanout(command: str, resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    insts = _instances()
    if not insts:
        return [{"ok": False, "error": "No Unbound resolvers configured (set UNBOUND_HOST etc.)"}]
    if resolvers:
        insts = [i for i in insts if i["name"] in resolvers]
    results: List[Dict[str, Any]] = []
    for inst in insts:
        try:
            out = _send(inst, command)
            if out.lower().startswith("error"):  # unbound-control error replies
                results.append({"unbound": inst["name"], "ok": False, "error": out})
            else:
                results.append({"unbound": inst["name"], "ok": True, "output": out})
        except Exception as e:  # noqa: BLE001 - surface per-resolver errors
            results.append({"unbound": inst["name"], "ok": False, "error": str(e)})
    return results


def register_tools(mcp, pihole_clients):  # pihole_clients unused; signature parity
    """Register Unbound resolver control tools with the MCP server."""

    @mcp.tool(
        name="unbound_status",
        description="Get Unbound resolver status (version, threads, uptime, modules) for each configured resolver.",
    )
    def unbound_status(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout("status", resolvers)

    @mcp.tool(
        name="unbound_stats",
        description="Get Unbound resolver statistics (queries, cache hits/misses, recursion times) parsed into key/value pairs. Non-resetting.",
    )
    def unbound_stats(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        results = _fanout("stats_noreset", resolvers)
        for r in results:
            if r.get("ok") and "output" in r:
                stats = {}
                for line in r["output"].splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        stats[k.strip()] = v.strip()
                r["stats"] = stats
                del r["output"]
        return results

    @mcp.tool(
        name="unbound_flush_domain",
        description="Flush a single domain (all record types) from the Unbound cache on each resolver. Use after a DNS change to force a fresh recursive lookup.",
    )
    def unbound_flush_domain(domain: str, resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout(f"flush {domain}", resolvers)

    @mcp.tool(
        name="unbound_flush_zone",
        description="Flush an entire zone (the name and everything under it) from the Unbound cache on each resolver. Pass '.' to flush the whole cache.",
    )
    def unbound_flush_zone(zone: str, resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout(f"flush_zone {zone}", resolvers)

    @mcp.tool(
        name="unbound_reload",
        description="Reload Unbound config and flush the cache on each resolver (unbound-control reload).",
    )
    def unbound_reload(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout("reload", resolvers)

    @mcp.tool(
        name="unbound_list_local_zones",
        description="List Unbound local-zones (resolver-level zone overrides) on each resolver.",
    )
    def unbound_list_local_zones(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout("list_local_zones", resolvers)

    @mcp.tool(
        name="unbound_list_local_data",
        description="List Unbound local-data records (resolver-level DNS overrides) on each resolver.",
    )
    def unbound_list_local_data(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout("list_local_data", resolvers)

    @mcp.tool(
        name="unbound_add_local_data",
        description=(
            "Add a resolver-level local DNS record to Unbound on each resolver. rr is a full "
            "resource record, e.g. 'host.lan. 3600 IN A 192.168.1.20'. Runtime change (not "
            "persisted to unbound.conf unless separately configured)."
        ),
    )
    def unbound_add_local_data(rr: str, resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout(f"local_data {rr}", resolvers)

    @mcp.tool(
        name="unbound_remove_local_data",
        description="Remove all resolver-level local DNS records for a name from Unbound on each resolver.",
    )
    def unbound_remove_local_data(name: str, resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout(f"local_data_remove {name}", resolvers)

    @mcp.tool(
        name="unbound_list_forwards",
        description="List Unbound forward-zones (upstream forwarding configuration) on each resolver.",
    )
    def unbound_list_forwards(resolvers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _fanout("list_forwards", resolvers)
