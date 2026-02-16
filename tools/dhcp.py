"""
Pi-hole MCP DHCP tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets


def register_tools(mcp, pihole_clients):
    """Register DHCP tools with the MCP server."""

    @mcp.tool(name="get_dhcp_leases", description="Get active DHCP leases from Pi-hole")
    def get_dhcp_leases(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all active DHCP leases from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].dhcp.get_leases()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="remove_dhcp_lease", description="Remove a DHCP lease by IP address")
    def remove_dhcp_lease(
        ip: str,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a DHCP lease by IP address.

        Args:
            ip: The IP address of the lease to remove
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].dhcp.remove_lease(ip)
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"Removed DHCP lease for {ip} on {len(results)} Pi-hole(s)",
            "results": results
        }
