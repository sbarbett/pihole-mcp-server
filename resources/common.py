"""
Pi-hole MCP resources
"""

from typing import Dict, List

def register_resources(mcp, pihole_clients, get_version):
    """Register common resources with the MCP server."""

    @mcp.resource("piholes://", description="Return information about all configured Pi-holes")
    def all_piholes() -> Dict[str, List[Dict[str, str]]]:
        """Return information about all configured Pi-holes
        
        Returns:
            Dict[str, List[Dict[str, str]]]: A dictionary containing a list of Pi-holes
        """
        piholes_list = [{"name": name, "url": client.connection.base_url} for name, client in pihole_clients.items()]
        return {"piholes": piholes_list}

    @mcp.resource("version://", description="Return the current version of the Pi-hole MCP server")
    def server_version() -> Dict[str, str]:
        """Return the current version of the Pi-hole MCP server
        
        Returns:
            Dict[str, str]: A dictionary containing the version of the Pi-hole MCP server
        """
        return {"version": get_version()} 