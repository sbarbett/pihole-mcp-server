"""
Pi-hole MCP configuration tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import (
    resolve_targets, create_confirmation_token, validate_confirmation_token, clean_expired_tokens
)


def register_tools(mcp, pihole_clients):
    """Register configuration-related tools with the MCP server."""

    @mcp.tool(name="list_local_dns", description="List local A and CNAME records from Pi-hole")
    def list_local_dns(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all local DNS records (A and CNAME) from Pi-hole

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].config.get_config_section('dns')
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="add_local_a_record", description="Add a local A record to Pi-hole")
    def add_local_a_record(host: str, ip: str, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a local A record to Pi-hole

        Args:
            host: The hostname for this A record (required)
            ip: The IP address for this A record (required)
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        all_added = []
        all_exists = []

        for target in targets:
            client = pihole_clients[target]
            try:
                response = client.config.get_config_section('dns/hosts')
                dns_config = response.get('config', {}).get('dns', {}).get('hosts', [])
                record = f"{ip} {host}"

                if record in dns_config:
                    all_exists.append({"pihole": target, "record": record})
                    continue

                client.config.add_local_a_record(host, ip)
                all_added.append({"pihole": target, "record": record})
            except Exception as e:
                return {"status": "error", "message": f"Error processing Pi-hole '{target}': {str(e)}"}

        if not all_added and all_exists:
            return {
                "status": "exists",
                "existing": all_exists,
                "message": f"Record '{ip} {host}' already exists in {len(all_exists)} Pi-hole(s)"
            }
        if all_added and not all_exists:
            return {
                "status": "added",
                "added": all_added,
                "message": f"Record added to {len(all_added)} Pi-hole(s)"
            }
        return {
            "status": "partial",
            "added": all_added,
            "existing": all_exists,
            "message": f"Record added to {len(all_added)} Pi-hole(s), already existed in {len(all_exists)} Pi-hole(s)"
        }

    @mcp.tool(name="add_local_cname_record", description="Add a local CNAME record to Pi-hole")
    def add_local_cname_record(host: str, target: str, ttl: int = 300, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a local CNAME record to Pi-hole

        Args:
            host: The hostname for this CNAME record (required)
            target: The target hostname this CNAME points to (required)
            ttl: Time-to-live value for the record, defaults to 300
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        all_added = []
        all_exists = []

        for target_pihole in targets:
            client = pihole_clients[target_pihole]
            try:
                response = client.config.get_config_section('dns/cnameRecords')
                dns_config = response.get('config', {}).get('dns', {}).get('cnameRecords', [])
                record = f"{host},{target},{ttl}"

                if record in dns_config:
                    all_exists.append({"pihole": target_pihole, "record": record})
                    continue

                client.config.add_local_cname(host, target, ttl)
                all_added.append({"pihole": target_pihole, "record": record})
            except Exception as e:
                return {"status": "error", "message": f"Error processing Pi-hole '{target_pihole}': {str(e)}"}

        if not all_added and all_exists:
            return {
                "status": "exists",
                "existing": all_exists,
                "message": f"CNAME '{host} -> {target},{ttl}' already exists in {len(all_exists)} Pi-hole(s)"
            }
        if all_added and not all_exists:
            return {
                "status": "added",
                "added": all_added,
                "message": f"CNAME record added to {len(all_added)} Pi-hole(s)"
            }
        return {
            "status": "partial",
            "added": all_added,
            "existing": all_exists,
            "message": f"CNAME record added to {len(all_added)} Pi-hole(s), already existed in {len(all_exists)} Pi-hole(s)"
        }

    @mcp.tool(name="remove_local_a_record", description="Remove a local A record from Pi-hole with confirmation token")
    def remove_local_a_record(host: str, confirm: Optional[str] = None, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a local A record from Pi-hole with confirmation token

        Two-step process:
        1. First call with confirm=None to preview and get a confirmation token
        2. Second call with confirm=<token> to perform the actual deletion

        Args:
            host: The hostname for this A record (required)
            confirm: Confirmation token from the preview step
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        """
        clean_expired_tokens()
        key = f"a_record:{host}"

        if confirm is not None:
            context = validate_confirmation_token(confirm, key)
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token. Please request deletion again."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            all_deleted = []
            for deletion_info in context["records"]:
                target_pihole = deletion_info["pihole"]
                ip = deletion_info["ip"]
                try:
                    pihole_clients[target_pihole].config.remove_local_a_record(host, ip)
                    all_deleted.append(deletion_info)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "deleted": all_deleted,
                "message": f"Removed {len(all_deleted)} record(s) from {len(set(r['pihole'] for r in all_deleted))} Pi-hole(s)"
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        all_planned = []
        for target in targets:
            try:
                response = pihole_clients[target].config.get_config_section('dns/hosts')
                dns_config = response.get('config', {}).get('dns', {}).get('hosts', [])

                for record in dns_config:
                    parts = record.split(' ', 1)
                    if len(parts) == 2 and parts[1] == host:
                        all_planned.append({
                            "pihole": target,
                            "record": record,
                            "ip": parts[0],
                            "host": host
                        })
            except Exception as e:
                return {"status": "error", "message": f"Error processing Pi-hole '{target}': {str(e)}"}

        if not all_planned:
            return {"status": "not_found", "message": f"No A records for '{host}' exist in any selected Pi-hole; nothing to delete"}

        token = create_confirmation_token(key, {"records": all_planned})
        return {
            "status": "pending_deletion",
            "planned": all_planned,
            "confirmationToken": token,
            "message": f"To confirm deletion of {len(all_planned)} record(s) from {len(set(r['pihole'] for r in all_planned))} Pi-hole(s), call again with confirm='{token}'"
        }

    @mcp.tool(name="remove_local_cname_record", description="Remove a local CNAME record from Pi-hole with confirmation token")
    def remove_local_cname_record(host: str, confirm: Optional[str] = None, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a local CNAME record from Pi-hole with confirmation token

        Two-step process:
        1. First call with confirm=None to preview and get a confirmation token
        2. Second call with confirm=<token> to perform the actual deletion

        Args:
            host: The hostname for this CNAME record (required)
            confirm: Confirmation token from the preview step
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        """
        clean_expired_tokens()
        key = f"cname_record:{host}"

        if confirm is not None:
            context = validate_confirmation_token(confirm, key)
            if context is None:
                return {"status": "invalid_token", "message": "Invalid or expired confirmation token. Please request deletion again."}
            if "error" in context:
                return {"status": "invalid_token", "message": context["error"]}

            all_deleted = []
            for deletion_info in context["records"]:
                target_pihole = deletion_info["pihole"]
                target = deletion_info["target"]
                ttl = deletion_info["ttl"]
                try:
                    pihole_clients[target_pihole].config.remove_local_cname(host, target, ttl)
                    all_deleted.append(deletion_info)
                except Exception:
                    pass

            return {
                "status": "deleted",
                "deleted": all_deleted,
                "message": f"Removed {len(all_deleted)} CNAME record(s) from {len(set(r['pihole'] for r in all_deleted))} Pi-hole(s)"
            }

        # Preview
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        all_planned = []
        for target_pihole in targets:
            try:
                response = pihole_clients[target_pihole].config.get_config_section('dns/cnameRecords')
                dns_config = response.get('config', {}).get('dns', {}).get('cnameRecords', [])

                for record in dns_config:
                    parts = record.split(',')
                    if len(parts) >= 1 and parts[0] == host:
                        record_target = parts[1] if len(parts) > 1 else ""
                        ttl = int(parts[2]) if len(parts) > 2 else 300
                        all_planned.append({
                            "pihole": target_pihole,
                            "record": record,
                            "host": host,
                            "target": record_target,
                            "ttl": ttl
                        })
            except Exception as e:
                return {"status": "error", "message": f"Error processing Pi-hole '{target_pihole}': {str(e)}"}

        if not all_planned:
            return {"status": "not_found", "message": f"No CNAME records for '{host}' exist in any selected Pi-hole"}

        token = create_confirmation_token(key, {"records": all_planned})
        return {
            "status": "pending_deletion",
            "planned": all_planned,
            "confirmationToken": token,
            "message": f"To confirm deletion of {len(all_planned)} CNAME record(s) from {len(set(r['pihole'] for r in all_planned))} Pi-hole(s), call again with confirm='{token}'"
        }

    @mcp.tool(name="get_config", description="Get Pi-hole configuration settings")
    def get_config(
        section: Optional[str] = None,
        detailed: bool = False,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Pi-hole configuration settings.

        Args:
            section: Optional config section to retrieve (e.g. "dns", "webserver", "dhcp").
                     If None, returns the full configuration.
            detailed: If True, return detailed configuration with descriptions
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                if section:
                    data = pihole_clients[name].config.get_config_section(section, detailed)
                else:
                    data = pihole_clients[name].config.get_config(detailed)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="update_config", description="Update Pi-hole configuration settings")
    def update_config(
        config_changes: Dict[str, Any],
        pihole: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Pi-hole configuration settings.

        Args:
            config_changes: Dictionary of configuration changes to apply.
                           Example: {"dns": {"blockingEnabled": True}}
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for target in targets:
            try:
                data = pihole_clients[target].config.update_config(config_changes)
                results.append({"pihole": target, "data": data})
            except Exception as e:
                results.append({"pihole": target, "error": str(e)})

        return {
            "status": "success",
            "message": f"Configuration updated on {len(results)} Pi-hole(s)",
            "results": results
        }
