"""
Pi-hole MCP network info tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets


def register_tools(mcp, pihole_clients):
    """Register network info tools with the MCP server."""

    @mcp.tool(name="get_network_devices", description="Get network devices discovered by Pi-hole")
    def get_network_devices(
        max_devices: Optional[int] = None,
        max_addresses: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get network devices discovered by Pi-hole.

        Args:
            max_devices: Optional maximum number of devices to return
            max_addresses: Optional maximum number of addresses per device
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].network_info.get_devices(max_devices, max_addresses)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="delete_network_device", description="Remove a device from Pi-hole's network table")
    def delete_network_device(
        device_id: int,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a device from Pi-hole's network table.

        Args:
            device_id: The device ID to remove
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].network_info.delete_device(device_id)
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"Device {device_id} removed from {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="get_network_info", description="Get network configuration (gateway, interfaces, routes)")
    def get_network_info(
        detailed: bool = False,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get network configuration including gateway, interfaces, and routes.

        Args:
            detailed: If True, return detailed information
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            client = pihole_clients[name]
            info = {}
            try:
                info["gateway"] = client.network_info.get_gateway(detailed)
            except Exception as e:
                info["gateway_error"] = str(e)
            try:
                info["interfaces"] = client.network_info.get_interfaces(detailed)
            except Exception as e:
                info["interfaces_error"] = str(e)
            try:
                info["routes"] = client.network_info.get_routes(detailed)
            except Exception as e:
                info["routes_error"] = str(e)

            result.append({"pihole": name, "data": info})
        return result
