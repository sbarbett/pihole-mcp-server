"""
Pi-hole MCP metrics tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets


def register_tools(mcp, pihole_clients):
    """Register metrics-related tools with the MCP server."""

    @mcp.tool(name="list_queries", description="Fetch recent DNS query history with filtering options")
    def list_queries(
        piholes: Optional[List[str]] = None,
        length: int = 10,
        from_ts: Optional[int] = None,
        until_ts: Optional[int] = None,
        upstream: Optional[str] = None,
        domain: Optional[str] = None,
        client_filter: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch the recent DNS query history from Pi-hole with filtering options

        By default returns the most recent 10 queries, but this can be changed
        using the length parameter. The results can be paginated using the cursor
        parameter, which is returned with each query result.

        For domain and client_filter parameters, you can use wildcards (*) at any position
        to match partial strings. For example:
          - "*google*" would match any domain containing "google"
          - "*.com" would match all .com domains
          - "192.168.1.*" would match all clients in that subnet

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
            length: Number of queries to retrieve (default: 10)
            from_ts: Unix timestamp to filter queries from this time onward
            until_ts: Unix timestamp to filter queries up to this time
            upstream: Filter queries sent to a specific upstream destination (may be "cache", "blocklist", or "permitted")
            domain: Filter queries for specific domains, supports wildcards (*)
            client_filter: Filter queries originating from a specific client, supports wildcards (*)
            cursor: Cursor for pagination to fetch the next chunk of results
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.metrics.get_queries(
                    length=length,
                    from_ts=from_ts,
                    until_ts=until_ts,
                    upstream=upstream,
                    domain=domain,
                    client=client_filter,
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
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_query_suggestions()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="list_query_history", description="Get activity graph data for Pi-hole queries over time")
    def list_query_history(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get activity graph data showing the distribution of queries over time

        This data is used to generate the total queries over time graph in the Pi-hole dashboard.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_history()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_stats_summary", description="Get Pi-hole activity summary statistics")
    def get_stats_summary(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get an overview of Pi-hole activity including total queries, blocked queries,
        percentage blocked, and domains on blocklists.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_summary()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_top_domains", description="Get top queried or blocked domains from Pi-hole")
    def get_top_domains(
        blocked: Optional[bool] = None,
        count: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top queried or top blocked domains.

        Args:
            blocked: If True, return top blocked domains. If False/None, return top queried domains.
            count: Optional number of results to return
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_top_domains(blocked, count)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_top_clients", description="Get top DNS query clients from Pi-hole")
    def get_top_clients(
        blocked: Optional[bool] = None,
        count: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top DNS query clients.

        Args:
            blocked: If True, return top blocked clients. If False/None, return top querying clients.
            count: Optional number of results to return
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_top_clients(blocked, count)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_stats_upstreams", description="Get upstream DNS server statistics from Pi-hole")
    def get_stats_upstreams(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get statistics about upstream DNS servers used by Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_upstreams()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_query_types", description="Get DNS query type distribution from Pi-hole")
    def get_query_types(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get the distribution of DNS query types (A, AAAA, PTR, etc.).

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_query_types()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_recent_blocked", description="Get recently blocked domains from Pi-hole")
    def get_recent_blocked(
        count: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recently blocked domains.

        Args:
            count: Optional number of results to return
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_stats_recent_blocked(count)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_history_clients", description="Get per-client activity history from Pi-hole")
    def get_history_clients(
        clients: int = 20,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get per-client activity data over time.

        Args:
            clients: Maximum number of clients to include (default 20)
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].metrics.get_history_clients(clients)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_database_stats", description="Get long-term database statistics from Pi-hole")
    def get_database_stats(
        start: int,
        end: int,
        stat_type: str = "summary",
        blocked: Optional[bool] = None,
        count: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get long-term database statistics for a time range.

        Args:
            start: Unix timestamp for the start of the range
            end: Unix timestamp for the end of the range
            stat_type: Type of stats: "summary", "query_types", "top_domains", "top_clients", "upstreams", "history", "history_clients"
            blocked: For top_domains/top_clients: if True, return blocked entries
            count: For top_domains/top_clients: max number of results
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        valid_types = ("summary", "query_types", "top_domains", "top_clients", "upstreams", "history", "history_clients")
        if stat_type not in valid_types:
            return [{"status": "error", "message": f"stat_type must be one of: {', '.join(valid_types)}"}]

        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        method_map = {
            "summary": lambda m: m.get_stats_database_summary(start, end),
            "query_types": lambda m: m.get_stats_database_query_types(start, end),
            "top_domains": lambda m: m.get_stats_database_top_domains(start, end, blocked, count),
            "top_clients": lambda m: m.get_stats_database_top_clients(start, end, blocked, count),
            "upstreams": lambda m: m.get_stats_database_upstreams(start, end),
            "history": lambda m: m.get_history_database(start, end),
            "history_clients": lambda m: m.get_history_database_clients(start, end),
        }

        result = []
        for name in targets:
            try:
                data = method_map[stat_type](pihole_clients[name].metrics)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result
