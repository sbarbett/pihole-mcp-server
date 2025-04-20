"""
Pi-hole MCP metrics tools
"""

from typing import List, Dict, Optional, Any

def register_tools(mcp, pihole_clients):
    """Register metrics-related tools with the MCP server."""

    @mcp.tool(name="list_queries", description="Fetch recent DNS query history with filtering options")
    def list_queries(
        piholes: Optional[List[str]] = None,
        length: int = 100,
        from_ts: Optional[int] = None,
        until_ts: Optional[int] = None,
        upstream: Optional[str] = None,
        domain: Optional[str] = None,
        client_filter: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch the recent DNS query history from Pi-hole with filtering options
        
        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
            length: Number of queries to retrieve (default: 100)
            from_ts: Unix timestamp to filter queries from this time onward
            until_ts: Unix timestamp to filter queries up to this time
            upstream: Filter queries sent to a specific upstream destination
            domain: Filter queries for specific domains, supports wildcards (*)
            client_filter: Filter queries originating from a specific client
            cursor: Cursor for pagination to fetch the next chunk of results
        """
        result = []
        
        # Determine which Pi-holes to query
        targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
        
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.metrics.get_queries(
                    length=length,
                    from_ts=from_ts,
                    until_ts=until_ts,
                    upstream=upstream,
                    domain=domain,
                    client=client_filter,  # Use client_filter to avoid name conflict with client variable
                    cursor=cursor
                )
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        
        return result

    @mcp.tool(name="list_query_suggestions", description="Get query filter suggestions for Pi-hole query data")
    def list_query_suggestions(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get query filter suggestions for all available filters from Pi-hole
        
        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        
        Returns:
            List of dictionaries containing suggestions for domains, clients, upstreams, query types, statuses, replies, and dnssec options
        """
        result = []
        
        # Determine which Pi-holes to query
        targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
        
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.metrics.get_query_suggestions()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        
        return result

    @mcp.tool(name="list_query_history", description="Get activity graph data for Pi-hole queries over time")
    def list_query_history(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get activity graph data showing the distribution of queries over time
        
        This data is used to generate the total queries over time graph in the Pi-hole dashboard.
        The sum of the values in the individual data arrays may be smaller than the total number
        of queries for the corresponding timestamp. The remaining queries are ones that do not fit
        into the shown categories (e.g. database busy, unknown status queries, etc.).
        
        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        
        Returns:
            List of dictionaries containing activity graph data for each Pi-hole
        """
        result = []
        
        # Determine which Pi-holes to query
        targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
        
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.metrics.get_history()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        
        return result 