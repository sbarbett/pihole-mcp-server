"""
Pi-hole MCP tool discovery resource
"""

from typing import Dict, List

def register_resources(mcp):
    """Register tool discovery resources with the MCP server."""
    
    @mcp.resource("list-tools://")
    def list_tool_categories() -> List[Dict[str, str]]:
        """Return a list of all tool categories available in the Pi-hole MCP server.
        
        This is the top-level discovery endpoint. When presenting these results to a user,
        inform them that they can get more details about tools in a specific category by
        using list-tools://<category> (e.g., list-tools://metrics).
        """
        # Simple static response with the two known categories
        return [
            {"name": "metrics", "description": "Pi-hole activity metrics"},
            {"name": "config", "description": "Configuration retrieval and updates"}
        ]
    
    @mcp.resource("list-tools://{category}")
    def list_category_tools(category: str) -> List[Dict[str, str]]:
        """Return a list of all tools in a specific category."""
        if category == "metrics":
            return [
                {"name": "list_queries", "description": "Retrieve query log entries"},
                {"name": "list_query_history", "description": "Get time-series of query counts"},
                {"name": "list_query_suggestions", "description": "Suggest popular domains"}
            ]
        elif category == "config":
            return [
                {"name": "list_local_dns", "description": "List local A and CNAME records from Pi-hole"}
            ]
        else:
            # Return a 404 error for unknown categories
            return mcp.not_found(f"Category '{category}' not found") 