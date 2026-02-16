"""
Pi-hole MCP DNS control tools (blocking status)
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets


def register_tools(mcp, pihole_clients):
    """Register DNS control tools with the MCP server."""

    @mcp.tool(name="get_blocking_status", description="Get the current DNS blocking status from Pi-hole")
    def get_blocking_status(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get the current DNS blocking status from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].dns_control.get_blocking_status()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="set_blocking_status", description="Enable or disable Pi-hole DNS blocking")
    def set_blocking_status(
        blocking: bool,
        timer: Optional[int] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enable or disable Pi-hole DNS blocking.

        Args:
            blocking: True to enable blocking, False to disable
            timer: Optional duration in seconds. When set, blocking reverts after this time.
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].dns_control.set_blocking_status(blocking, timer)
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        action = "enabled" if blocking else "disabled"
        timer_msg = f" for {timer} seconds" if timer else ""
        return {
            "status": "success",
            "message": f"Blocking {action}{timer_msg} on {len(results)} Pi-hole(s)",
            "results": results
        }
