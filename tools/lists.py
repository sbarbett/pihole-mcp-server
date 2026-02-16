"""
Pi-hole MCP list management tools (blocklists/allowlists)
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets, create_confirmation_token, validate_confirmation_token, clean_expired_tokens


def register_tools(mcp, pihole_clients):
    """Register list management tools with the MCP server."""

    @mcp.tool(name="get_lists", description="Get all blocklists and allowlists from Pi-hole")
    def get_lists(
        list_type: Optional[str] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all blocklists and/or allowlists from Pi-hole.

        Args:
            list_type: Optional filter: "block" or "allow". If None, returns all lists.
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].list_management.get_lists(list_type)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="add_list", description="Add a blocklist or allowlist URL to Pi-hole")
    def add_list(
        address: str,
        list_type: str,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a blocklist or allowlist URL to Pi-hole.

        Args:
            address: URL of the list to add
            list_type: "block" or "allow"
            comment: Optional description
            groups: Optional list of group IDs to associate with
            enabled: Whether the list is enabled (default True)
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        if list_type not in ("block", "allow"):
            return {"status": "error", "message": "list_type must be 'block' or 'allow'"}

        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].list_management.add_list(
                    address, list_type, comment, groups, enabled
                )
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"List '{address}' ({list_type}) added to {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="update_list", description="Update an existing list entry in Pi-hole")
    def update_list(
        address: str,
        list_type: str,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing list entry in Pi-hole.

        Args:
            address: URL of the list to update
            list_type: "block" or "allow"
            comment: Optional new comment
            groups: Optional new group IDs
            enabled: Whether the list is enabled
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].list_management.update_list(
                    address, list_type, comment, groups, enabled
                )
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"List '{address}' updated on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="delete_list", description="Delete a list entry from Pi-hole with confirmation token")
    def delete_list(
        address: str,
        list_type: str,
        confirm: Optional[str] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a list entry from Pi-hole with confirmation.

        Two-step process:
        1. Call with confirm=None to preview and get a confirmation token
        2. Call with confirm=<token> to perform the deletion

        Args:
            address: URL of the list to delete
            list_type: "block" or "allow"
            confirm: Confirmation token from preview step
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        clean_expired_tokens()
        key = f"list:{list_type}:{address}"

        if confirm is not None:
            context = validate_confirmation_token(confirm, key)
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            deleted = []
            for target in context["targets"]:
                try:
                    pihole_clients[target].list_management.delete_list(address, list_type)
                    deleted.append(target)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "message": f"List '{address}' ({list_type}) deleted from {len(deleted)} Pi-hole(s)",
                "deleted_from": deleted
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        found_on = []
        for target in targets:
            try:
                pihole_clients[target].list_management.get_list(address, list_type)
                found_on.append(target)
            except Exception:
                pass

        if not found_on:
            return {"status": "not_found", "message": f"List '{address}' ({list_type}) not found"}

        token = create_confirmation_token(key, {"targets": found_on})
        return {
            "status": "pending_deletion",
            "address": address,
            "list_type": list_type,
            "found_on": found_on,
            "confirmationToken": token,
            "message": f"List found on {len(found_on)} Pi-hole(s). Call again with confirm='{token}' to delete."
        }

    @mcp.tool(name="search_list", description="Search for a domain across all Pi-hole blocklists and allowlists")
    def search_list(
        domain: str,
        num: Optional[int] = None,
        partial: bool = False,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for a domain across all Pi-hole blocklists and allowlists.

        Args:
            domain: Domain to search for
            num: Optional maximum number of results
            partial: If True, search for partial matches
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].list_management.search_list(domain, num, partial)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result
