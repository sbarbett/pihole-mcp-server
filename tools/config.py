"""
Pi-hole MCP configuration tools
"""

from typing import List, Dict, Optional, Any

def register_tools(mcp, pihole_clients):
    """Register configuration-related tools with the MCP server."""

    @mcp.tool(name="list_local_dns", description="List local A and CNAME records from Pi-hole")
    def list_local_dns(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all local DNS records (A and CNAME) from Pi-hole
        
        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        """
        result = []
        
        # Determine which Pi-holes to query
        targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
        
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.config.get_config_section('dns')
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        
        return result 