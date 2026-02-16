"""
Pi-hole MCP system info, diagnostics, and actions tools
"""

from typing import List, Dict, Optional, Any
from tools.confirmation import resolve_targets


def register_tools(mcp, pihole_clients):
    """Register system info, diagnostics, and action tools with the MCP server."""

    @mcp.tool(name="get_system_info", description="Get comprehensive system information from Pi-hole")
    def get_system_info(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get comprehensive system information including FTL, host, system params,
        version details, sensors, and metrics.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            client = pihole_clients[name]
            info = {}
            try:
                info["version"] = client.ftl_info.get_version()
            except Exception as e:
                info["version_error"] = str(e)
            try:
                info["system"] = client.ftl_info.get_system_info()
            except Exception as e:
                info["system_error"] = str(e)
            try:
                info["host"] = client.ftl_info.get_host_info()
            except Exception as e:
                info["host_error"] = str(e)
            try:
                info["ftl"] = client.ftl_info.get_ftl_info()
            except Exception as e:
                info["ftl_error"] = str(e)
            try:
                info["sensors"] = client.ftl_info.get_sensors_info()
            except Exception as e:
                info["sensors_error"] = str(e)
            try:
                info["metrics"] = client.ftl_info.get_metrics_info()
            except Exception as e:
                info["metrics_error"] = str(e)

            result.append({"pihole": name, "data": info})
        return result

    @mcp.tool(name="get_pihole_version", description="Get Pi-hole version details")
    def get_pihole_version(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get Pi-hole version details (core, FTL, web).

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].ftl_info.get_version()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_padd_summary", description="Get PADD-style dashboard summary from Pi-hole")
    def get_padd_summary(
        full: bool = False,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a PADD-style dashboard summary of Pi-hole status.

        Args:
            full: If True, return full detailed summary. Default is condensed.
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].get_padd_summary(full)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_diagnosis_messages", description="Get diagnostic messages from Pi-hole")
    def get_diagnosis_messages(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all diagnostic/warning messages from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].ftl_info.get_diagnosis_messages()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_database_info", description="Get long-term database statistics from Pi-hole")
    def get_database_info(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get long-term database statistics from Pi-hole.

        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        result = []
        for name in targets:
            try:
                data = pihole_clients[name].ftl_info.get_database_info()
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="get_logs", description="Get Pi-hole logs (dnsmasq, FTL, or webserver)")
    def get_logs(
        log_type: str = "dnsmasq",
        next_id: Optional[int] = None,
        piholes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Pi-hole logs.

        Args:
            log_type: Type of log to retrieve: "dnsmasq", "ftl", or "webserver"
            next_id: Optional ID to fetch logs after (for pagination)
            piholes: Optional list of Pi-hole names to query. If None, query all.
        """
        if log_type not in ("dnsmasq", "ftl", "webserver"):
            return [{"status": "error", "message": "log_type must be 'dnsmasq', 'ftl', or 'webserver'"}]

        targets, err = resolve_targets(pihole_clients, piholes=piholes)
        if err:
            return [err]

        log_methods = {
            "dnsmasq": "get_dnsmasq_logs",
            "ftl": "get_ftl_logs",
            "webserver": "get_webserver_logs",
        }

        result = []
        for name in targets:
            try:
                method = getattr(pihole_clients[name].ftl_info, log_methods[log_type])
                data = method(next_id)
                result.append({"pihole": name, "data": data})
            except Exception as e:
                result.append({"pihole": name, "error": str(e)})
        return result

    @mcp.tool(name="run_gravity", description="Update Pi-hole gravity (re-download and process blocklists)")
    def run_gravity(pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Update Pi-hole gravity - re-download and process all configured blocklists.
        This may take some time to complete.

        Args:
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].actions.run_gravity()
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"Gravity update triggered on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="restart_dns", description="Restart Pi-hole's FTL DNS resolver")
    def restart_dns(pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Restart Pi-hole's FTL DNS resolver.

        Args:
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].actions.restart_dns()
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"DNS restart triggered on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="flush_arp", description="Flush Pi-hole's network table (ARP cache)")
    def flush_arp(pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Flush Pi-hole's network table (ARP cache).

        Args:
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].actions.flush_arp()
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"ARP cache flushed on {len(results)} Pi-hole(s)",
            "results": results
        }

    @mcp.tool(name="flush_logs", description="Flush Pi-hole's DNS query logs")
    def flush_logs(pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Flush Pi-hole's DNS query logs.

        Args:
            pihole: Optional Pi-hole name. If None, apply to all.
        """
        targets, err = resolve_targets(pihole_clients, pihole=pihole)
        if err:
            return err

        results = []
        for name in targets:
            try:
                data = pihole_clients[name].actions.flush_logs()
                results.append({"pihole": name, "data": data})
            except Exception as e:
                results.append({"pihole": name, "error": str(e)})

        return {
            "status": "success",
            "message": f"Logs flushed on {len(results)} Pi-hole(s)",
            "results": results
        }
