"""
Pi-hole MCP blocking & blocklist control tools (custom extension).

Adds the controls the upstream server lacks: enable/disable ad-blocking (with
timer), allow/deny domain rules, adlist (blocklist) management, and gravity
rebuild. Follows the same register_tools(mcp, pihole_clients) pattern and the
same {"pihole": name, "data"|"error": ...} result shape as tools/config.py.

Write operations default to every configured Pi-hole (pihole=None). With a
single primary configured, nebula-sync propagates changes to replicas.
"""

from typing import List, Dict, Optional, Any


def register_tools(mcp, pihole_clients):
    """Register blocking / blocklist / domain-rule control tools."""

    def _targets(piholes):
        if piholes is None:
            return list(pihole_clients.keys())
        return [p for p in piholes if p in pihole_clients]

    def _run(targets, fn):
        result = []
        for name in targets:
            try:
                result.append({"pihole": name, "data": fn(pihole_clients[name])})
            except Exception as e:  # noqa: BLE001 - surface per-Pi-hole errors
                result.append({"pihole": name, "error": str(e)})
        return result

    # --- Ad-blocking on/off -------------------------------------------------

    @mcp.tool(
        name="get_blocking_status",
        description="Get Pi-hole ad-blocking status (enabled/disabled and any active timer) for each Pi-hole.",
    )
    def get_blocking_status(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return _run(_targets(piholes), lambda c: c.dns_control.get_blocking_status())

    @mcp.tool(
        name="set_blocking",
        description=(
            "Enable or disable Pi-hole ad-blocking. Optional timer (seconds): "
            "e.g. enabled=false, timer=300 disables blocking for 5 minutes then "
            "auto-re-enables. Omit timer for a permanent change."
        ),
    )
    def set_blocking(
        enabled: bool, timer: Optional[int] = None, pihole: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(targets, lambda c: c.dns_control.set_blocking_status(enabled, timer))

    # --- Adlists / blocklists ----------------------------------------------

    @mcp.tool(
        name="list_blocklists",
        description="List adlists on Pi-hole. list_type: 'block' or 'allow' (omit for all).",
    )
    def list_blocklists(
        list_type: Optional[str] = None, piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        return _run(_targets(piholes), lambda c: c.list_management.get_lists(list_type))

    @mcp.tool(
        name="add_blocklist",
        description=(
            "Add an adlist to Pi-hole by URL. list_type: 'block' (default) or "
            "'allow'. Run update_gravity afterwards to apply."
        ),
    )
    def add_blocklist(
        address: str,
        list_type: str = "block",
        comment: Optional[str] = None,
        pihole: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(targets, lambda c: c.list_management.add_list(address, list_type, comment))

    @mcp.tool(
        name="remove_blocklist",
        description=(
            "Remove an adlist from Pi-hole by URL. list_type: 'block' or 'allow'. "
            "Run update_gravity afterwards to apply."
        ),
    )
    def remove_blocklist(
        address: str, list_type: str, pihole: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(targets, lambda c: c.list_management.delete_list(address, list_type))

    @mcp.tool(
        name="update_gravity",
        description="Run gravity to rebuild Pi-hole's blocklists (apply adlist changes). May take a bit.",
    )
    def update_gravity(pihole: Optional[str] = None) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(targets, lambda c: c.actions.run_gravity())

    # --- Allow / deny domain rules -----------------------------------------

    @mcp.tool(
        name="add_domain_rule",
        description=(
            "Add an allow or deny domain rule. domain_type: 'allow' or 'deny'. "
            "kind: 'exact' or 'regex'. Takes effect immediately (no gravity needed)."
        ),
    )
    def add_domain_rule(
        domain: str,
        domain_type: str,
        kind: str = "exact",
        comment: Optional[str] = None,
        pihole: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(
            targets,
            lambda c: c.domain_management.add_domain(domain, domain_type, kind, comment),
        )

    @mcp.tool(
        name="remove_domain_rule",
        description="Remove an allow/deny domain rule. domain_type: 'allow' or 'deny'. kind: 'exact' or 'regex'.",
    )
    def remove_domain_rule(
        domain: str, domain_type: str, kind: str = "exact", pihole: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        targets = _targets(None) if pihole is None else _targets([pihole])
        return _run(
            targets,
            lambda c: c.domain_management.delete_domain(domain, domain_type, kind),
        )

    @mcp.tool(
        name="get_domain_rule",
        description="Look up a specific allow/deny domain rule. domain_type: 'allow' or 'deny'. kind: 'exact' or 'regex'.",
    )
    def get_domain_rule(
        domain: str,
        domain_type: str,
        kind: str = "exact",
        piholes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        return _run(
            _targets(piholes),
            lambda c: c.domain_management.get_domain(domain, domain_type, kind),
        )
