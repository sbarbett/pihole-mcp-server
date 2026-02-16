"""
Pi-hole MCP group management tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets, create_confirmation_token, validate_confirmation_token, clean_expired_tokens


def register_tools(mcp, pihole_clients):
    """Register group management tools with the MCP server."""

    @mcp.tool(name="get_groups", description="Get all groups from Pi-hole")
    def get_groups(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all groups from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].group_management.get_groups()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="add_group", description="Add a new group to Pi-hole")
    def add_group(
        name: str,
        comment: Optional[str] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new group to Pi-hole.

        Args:
            name: Name for the new group
            comment: Optional description/comment for the group
            enabled: Whether the group is enabled (default True)
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].group_management.add_group(name, comment, enabled)
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Group '{name}' added to {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="update_group", description="Update an existing group in Pi-hole")
    def update_group(
        name: str,
        new_name: Optional[str] = None,
        comment: Optional[str] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing group in Pi-hole.

        Args:
            name: Current name of the group to update
            new_name: Optional new name for the group
            comment: Optional new comment
            enabled: Whether the group is enabled
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].group_management.update_group(name, new_name, comment, enabled)
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Group '{name}' updated on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="delete_group", description="Delete a group from Pi-hole with confirmation token")
    def delete_group(
        name: str,
        confirm: Optional[str] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a group from Pi-hole with confirmation.

        Two-step process:
        1. Call with confirm=None to preview and get a confirmation token
        2. Call with confirm=<token> to perform the deletion

        Args:
            name: Name of the group to delete
            confirm: Confirmation token from preview step
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        clean_expired_tokens()

        if confirm is not None:
            context = validate_confirmation_token(confirm, f"group:{name}")
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token. Please request deletion again."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            deleted = []
            for target in context["targets"]:
                try:
                    pihole_clients[target].group_management.delete_group(name)
                    deleted.append(target)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "message": f"Group '{name}' deleted from {len(deleted)} Pi-hole(s)",
                "deleted_from": deleted
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        found_on = []
        for target in targets:
            try:
                pihole_clients[target].group_management.get_group(name)
                found_on.append(target)
            except Exception:
                pass

        if not found_on:
            return {"status": "not_found", "message": f"Group '{name}' not found on any Pi-hole"}

        token = create_confirmation_token(f"group:{name}", {"targets": found_on})
        return {
            "status": "pending_deletion",
            "group": name,
            "found_on": found_on,
            "confirmationToken": token,
            "message": f"Group '{name}' found on {len(found_on)} Pi-hole(s). Call again with confirm='{token}' to delete."
        }
