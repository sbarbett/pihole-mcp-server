"""
Pi-hole MCP client management tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets, create_confirmation_token, validate_confirmation_token, clean_expired_tokens


def register_tools(mcp, pihole_clients):
    """Register client management tools with the MCP server."""

    @mcp.tool(name="get_clients", description="Get all configured clients from Pi-hole")
    def get_clients(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all configured clients from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].client_management.get_clients()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_client_suggestions", description="Get suggested clients based on known network devices")
    def get_client_suggestions(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get suggested clients based on known network devices.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].client_management.get_client_suggestions()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="add_client", description="Add a client to Pi-hole for group-based management")
    def add_client(
        client: str,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a client to Pi-hole for group-based management.

        Args:
            client: Client identifier (IP address, MAC address, hostname, or interface name)
            comment: Optional description
            groups: Optional list of group IDs to associate with
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].client_management.add_client(client, comment, groups)
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Client '{client}' added to {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="update_client", description="Update an existing client entry in Pi-hole")
    def update_client(
        client: str,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing client entry in Pi-hole.

        Args:
            client: Client identifier to update
            comment: Optional new comment
            groups: Optional new group IDs
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].client_management.update_client(client, comment, groups)
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Client '{client}' updated on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="delete_client", description="Delete a client from Pi-hole with confirmation token")
    def delete_client(
        client: str,
        confirm: Optional[str] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a client from Pi-hole with confirmation.

        Two-step process:
        1. Call with confirm=None to preview and get a confirmation token
        2. Call with confirm=<token> to perform the deletion

        Args:
            client: Client identifier to delete
            confirm: Confirmation token from preview step
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        clean_expired_tokens()
        key = f"client:{client}"

        if confirm is not None:
            context = validate_confirmation_token(confirm, key)
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            deleted = []
            for target in context["targets"]:
                try:
                    pihole_clients[target].client_management.delete_client(client)
                    deleted.append(target)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "message": f"Client '{client}' deleted from {len(deleted)} Pi-hole(s)",
                "deleted_from": deleted
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        found_on = []
        for target in targets:
            try:
                pihole_clients[target].client_management.get_client(client)
                found_on.append(target)
            except Exception:
                pass

        if not found_on:
            return {"status": "not_found", "message": f"Client '{client}' not found"}

        token = create_confirmation_token(key, {"targets": found_on})
        return {
            "status": "pending_deletion",
            "client": client,
            "found_on": found_on,
            "confirmationToken": token,
            "message": f"Client found on {len(found_on)} Pi-hole(s). Call again with confirm='{token}' to delete."
        }
