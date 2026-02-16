"""
Pi-hole MCP domain management tools (allow/deny lists)
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets, create_confirmation_token, validate_confirmation_token, clean_expired_tokens


def register_tools(mcp, pihole_clients):
    """Register domain management tools with the MCP server."""

    @mcp.tool(name="get_domains", description="Get all allow/deny domain entries from Pi-hole")
    def get_domains(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all domain entries (allow and deny, exact and regex) from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].domain_management.get_all_domains()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="add_domain", description="Add a domain to Pi-hole's allow or deny list")
    def add_domain(
        domain: str,
        domain_type: str,
        kind: str,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a domain to Pi-hole's allow or deny list.

        Args:
            domain: The domain to add (e.g. "example.com" or regex like "(^|\\.)example\\.com$")
            domain_type: "allow" or "deny"
            kind: "exact" for exact domain match, "regex" for regex pattern
            comment: Optional description
            groups: Optional list of group IDs to associate with
            enabled: Whether the entry is enabled (default True)
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        if domain_type not in ("allow", "deny"):
            return {"status": "error", "message": "domain_type must be 'allow' or 'deny'"}
        if kind not in ("exact", "regex"):
            return {"status": "error", "message": "kind must be 'exact' or 'regex'"}

        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].domain_management.add_domain(
                    domain, domain_type, kind, comment, groups, enabled
                )
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Domain '{domain}' ({domain_type}/{kind}) added to {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="update_domain", description="Update an existing domain entry in Pi-hole")
    def update_domain(
        domain: str,
        domain_type: str,
        kind: str,
        new_type: Optional[str] = None,
        new_kind: Optional[str] = None,
        comment: Optional[str] = None,
        groups: Optional[List[int]] = None,
        enabled: bool = True,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing domain entry in Pi-hole.

        Args:
            domain: The domain to update
            domain_type: Current type: "allow" or "deny"
            kind: Current kind: "exact" or "regex"
            new_type: Optional new type: "allow" or "deny"
            new_kind: Optional new kind: "exact" or "regex"
            comment: Optional new comment
            groups: Optional new group IDs
            enabled: Whether the entry is enabled
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].domain_management.update_domain(
                    domain, domain_type, kind, new_type, new_kind, comment, groups, enabled
                )
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Domain '{domain}' updated on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="delete_domain", description="Delete a domain entry from Pi-hole with confirmation token")
    def delete_domain(
        domain: str,
        domain_type: str,
        kind: str,
        confirm: Optional[str] = None,
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a domain entry from Pi-hole with confirmation.

        Two-step process:
        1. Call with confirm=None to preview and get a confirmation token
        2. Call with confirm=<token> to perform the deletion

        Args:
            domain: The domain to delete
            domain_type: "allow" or "deny"
            kind: "exact" or "regex"
            confirm: Confirmation token from preview step
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        clean_expired_tokens()
        key = f"domain:{domain_type}:{kind}:{domain}"

        if confirm is not None:
            context = validate_confirmation_token(confirm, key)
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            deleted = []
            for target in context["targets"]:
                try:
                    pihole_clients[target].domain_management.delete_domain(domain, domain_type, kind)
                    deleted.append(target)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "message": f"Domain '{domain}' ({domain_type}/{kind}) deleted from {len(deleted)} Pi-hole(s)",
                "deleted_from": deleted
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        found_on = []
        for target in targets:
            try:
                pihole_clients[target].domain_management.get_domain(domain, domain_type, kind)
                found_on.append(target)
            except Exception:
                pass

        if not found_on:
            return {"status": "not_found", "message": f"Domain '{domain}' ({domain_type}/{kind}) not found"}

        token = create_confirmation_token(key, {"targets": found_on})
        return {
            "status": "pending_deletion",
            "domain": domain,
            "domain_type": domain_type,
            "kind": kind,
            "found_on": found_on,
            "confirmationToken": token,
            "message": f"Domain found on {len(found_on)} Pi-hole(s). Call again with confirm='{token}' to delete."
        }
