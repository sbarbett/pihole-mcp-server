"""
Pi-hole MCP tool discovery resource
"""

from typing import Dict, List

def register_resources(mcp):
    """Register tool discovery resources with the MCP server."""

    @mcp.resource("list-tools://", description="Return a list of all tool categories available in the Pi-hole MCP server")
    def list_tool_categories() -> List[Dict[str, str]]:
        """Return a list of all tool categories available in the Pi-hole MCP server.

        This is the top-level discovery endpoint. When presenting these results to a user,
        inform them that they can get more details about tools in a specific category by
        using list-tools://<category> (e.g., list-tools://metrics).
        """
        return [
            {"name": "metrics", "description": "Pi-hole activity metrics, statistics, and query data"},
            {"name": "config", "description": "Configuration retrieval, updates, and local DNS record management"},
            {"name": "dns_control", "description": "DNS blocking status control"},
            {"name": "dhcp", "description": "DHCP lease management"},
            {"name": "groups", "description": "Group management for organizing policies"},
            {"name": "domains", "description": "Domain allow/deny list management"},
            {"name": "lists", "description": "Blocklist and allowlist management"},
            {"name": "clients", "description": "Client/device management and group assignment"},
            {"name": "system", "description": "System info, diagnostics, logs, and actions"},
            {"name": "network", "description": "Network device discovery and configuration info"},
        ]

    @mcp.resource("list-tools://{category}", description="Return a list of all tools in a specific category")
    def list_category_tools(category: str) -> List[Dict[str, str]]:
        """Return a list of all tools in a specific category.

        If an unknown category is requested, a 404 error is returned.
        """
        categories = {
            "metrics": [
                {"name": "list_queries", "description": "Retrieve query log entries with filtering"},
                {"name": "list_query_history", "description": "Get time-series of query counts"},
                {"name": "list_query_suggestions", "description": "Get filter suggestions for query data"},
                {"name": "get_stats_summary", "description": "Get activity summary (total queries, blocked, etc.)"},
                {"name": "get_top_domains", "description": "Get top queried or blocked domains"},
                {"name": "get_top_clients", "description": "Get top DNS query clients"},
                {"name": "get_stats_upstreams", "description": "Get upstream DNS server statistics"},
                {"name": "get_query_types", "description": "Get DNS query type distribution"},
                {"name": "get_recent_blocked", "description": "Get recently blocked domains"},
                {"name": "get_history_clients", "description": "Get per-client activity history"},
                {"name": "get_database_stats", "description": "Get long-term database statistics for a time range"},
            ],
            "config": [
                {"name": "list_local_dns", "description": "List local A and CNAME records"},
                {"name": "add_local_a_record", "description": "Add a local A record"},
                {"name": "add_local_cname_record", "description": "Add a local CNAME record"},
                {"name": "remove_local_a_record", "description": "Remove local A records with confirmation"},
                {"name": "remove_local_cname_record", "description": "Remove local CNAME records with confirmation"},
                {"name": "get_config", "description": "Get Pi-hole configuration settings"},
                {"name": "update_config", "description": "Update Pi-hole configuration settings"},
            ],
            "dns_control": [
                {"name": "get_blocking_status", "description": "Get current DNS blocking status"},
                {"name": "set_blocking_status", "description": "Enable or disable DNS blocking"},
            ],
            "dhcp": [
                {"name": "get_dhcp_leases", "description": "Get active DHCP leases"},
                {"name": "remove_dhcp_lease", "description": "Remove a DHCP lease by IP"},
            ],
            "groups": [
                {"name": "get_groups", "description": "Get all groups"},
                {"name": "add_group", "description": "Add a new group"},
                {"name": "update_group", "description": "Update an existing group"},
                {"name": "delete_group", "description": "Delete a group with confirmation"},
            ],
            "domains": [
                {"name": "get_domains", "description": "Get all allow/deny domain entries"},
                {"name": "add_domain", "description": "Add a domain to allow or deny list"},
                {"name": "update_domain", "description": "Update an existing domain entry"},
                {"name": "delete_domain", "description": "Delete a domain entry with confirmation"},
            ],
            "lists": [
                {"name": "get_lists", "description": "Get all blocklists and allowlists"},
                {"name": "add_list", "description": "Add a blocklist or allowlist URL"},
                {"name": "update_list", "description": "Update an existing list entry"},
                {"name": "delete_list", "description": "Delete a list entry with confirmation"},
                {"name": "search_list", "description": "Search for a domain across all lists"},
            ],
            "clients": [
                {"name": "get_clients", "description": "Get all configured clients"},
                {"name": "get_client_suggestions", "description": "Get suggested clients from network devices"},
                {"name": "add_client", "description": "Add a client for group-based management"},
                {"name": "update_client", "description": "Update an existing client entry"},
                {"name": "delete_client", "description": "Delete a client with confirmation"},
            ],
            "system": [
                {"name": "get_system_info", "description": "Get comprehensive system information"},
                {"name": "get_pihole_version", "description": "Get Pi-hole version details"},
                {"name": "get_padd_summary", "description": "Get PADD-style dashboard summary"},
                {"name": "get_diagnosis_messages", "description": "Get diagnostic messages"},
                {"name": "get_database_info", "description": "Get long-term database statistics"},
                {"name": "get_logs", "description": "Get Pi-hole logs (dnsmasq, FTL, webserver)"},
                {"name": "run_gravity", "description": "Update gravity (re-download blocklists)"},
                {"name": "restart_dns", "description": "Restart FTL DNS resolver"},
                {"name": "flush_arp", "description": "Flush network table (ARP cache)"},
                {"name": "flush_logs", "description": "Flush DNS query logs"},
            ],
            "network": [
                {"name": "get_network_devices", "description": "Get network devices discovered by Pi-hole"},
                {"name": "delete_network_device", "description": "Remove a device from network table"},
                {"name": "get_network_info", "description": "Get gateway, interfaces, and routes"},
            ],
        }

        if category in categories:
            return categories[category]
        else:
            return mcp.not_found(f"Category '{category}' not found")
