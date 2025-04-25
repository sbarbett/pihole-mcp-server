"""
Pi-hole MCP configuration tools
"""

from typing import List, Dict, Optional, Any

def register_tools(mcp, pihole_clients):
    """Register configuration-related tools with the MCP server."""

    @mcp.tool(name="list_local_dns", description="List local A and CNAME records from Pi-hole")
    def list_local_dns(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all local DNS records (A and CNAME) from Pi-hole
        
        Args:
            piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        """
        result = []
        
        # Determine which Pi-holes to query
        targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
        
        for name in targets:
            client = pihole_clients[name]
            try:
                data = client.config.get_config_section('dns')
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
        
        Returns:
            Dict with status ("added", "exists", or "error"),
            message, and added entries
        """
        # Determine which Pi-holes to target
        targets = [pihole] if pihole is not None else pihole_clients.keys()
        
        # Check if specified pihole exists
        if pihole is not None and pihole not in pihole_clients:
            return {
                "status": "error",
                "message": f"Pi-hole '{pihole}' not found"
            }
        
        all_added = []
        all_exists = []
        
        # Process each target Pi-hole
        for target in targets:
            client = pihole_clients[target]
            
            try:
                # Get current hosts section to check if record already exists
                response = client.config.get_config_section('dns/hosts')
                # Extract hosts from nested structure
                dns_config = response.get('config', {}).get('dns', {}).get('hosts', [])
                
                # Format the record
                record = f"{ip} {host}"
                
                # Check if the record already exists
                if record in dns_config:
                    all_exists.append({"pihole": target, "record": record})
                    continue
                
                # Add the record using the client's method
                client.config.add_local_a_record(host, ip)
                all_added.append({"pihole": target, "record": record})
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error processing Pi-hole '{target}': {str(e)}"
                }
        
        # Return appropriate response based on results
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
        
        # Mixed result - some added, some already existed
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
        
        Returns:
            Dict with status ("added", "exists", or "error"),
            message, and added entries
        """
        # Determine which Pi-holes to target
        targets = [pihole] if pihole is not None else pihole_clients.keys()
        
        # Check if specified pihole exists
        if pihole is not None and pihole not in pihole_clients:
            return {
                "status": "error",
                "message": f"Pi-hole '{pihole}' not found"
            }
        
        all_added = []
        all_exists = []
        
        # Process each target Pi-hole
        for target_pihole in targets:
            client = pihole_clients[target_pihole]
            
            try:
                # Get current CNAME records section
                response = client.config.get_config_section('dns/cnameRecords')
                # Extract cnameRecords from nested structure
                dns_config = response.get('config', {}).get('dns', {}).get('cnameRecords', [])
                
                # Format the record
                record = f"{host},{target},{ttl}"
                
                # Check if the record already exists
                if record in dns_config:
                    all_exists.append({"pihole": target_pihole, "record": record})
                    continue
                
                # Add the record using the client's method
                client.config.add_local_cname(host, target, ttl)
                all_added.append({"pihole": target_pihole, "record": record})
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error processing Pi-hole '{target_pihole}': {str(e)}"
                }
        
        # Return appropriate response based on results
        if not all_added and all_exists:
            return {
                "status": "exists",
                "existing": all_exists,
                "message": f"CNAME '{host} → {target},{ttl}' already exists in {len(all_exists)} Pi-hole(s)"
            }
        
        if all_added and not all_exists:
            return {
                "status": "added",
                "added": all_added,
                "message": f"CNAME record added to {len(all_added)} Pi-hole(s)"
            }
        
        # Mixed result - some added, some already existed
        return {
            "status": "partial",
            "added": all_added,
            "existing": all_exists,
            "message": f"CNAME record added to {len(all_added)} Pi-hole(s), already existed in {len(all_exists)} Pi-hole(s)"
        }
    
    @mcp.tool(name="remove_local_a_record", description="Remove a local A record from Pi-hole with confirmation")
    def remove_local_a_record(host: str, confirm: bool = False, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a local A record from Pi-hole with confirmation
        
        This requires a two-step process for safety:
        1. First call with confirm=false (default) returns what would be deleted
        2. Second call with confirm=true performs the actual deletion
        
        Args:
            host: The hostname for this A record (required)
            confirm: Set to true to confirm deletion, false for preview only
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        
        Returns:
            Dict with status ("not_found", "pending_deletion", "deleted", or "error"),
            message, and planned/deleted entries
        """
        # Determine which Pi-holes to target
        targets = [pihole] if pihole is not None else pihole_clients.keys()
        
        # Check if specified pihole exists
        if pihole is not None and pihole not in pihole_clients:
            return {
                "status": "error",
                "message": f"Pi-hole '{pihole}' not found"
            }
        
        all_planned = []
        all_deleted = []
        record_found = False
        
        # Process each target Pi-hole
        for target in targets:
            client = pihole_clients[target]
            
            try:
                # Get current hosts section
                response = client.config.get_config_section('dns/hosts')
                # Extract hosts from nested structure
                dns_config = response.get('config', {}).get('dns', {}).get('hosts', [])
                
                # Find all records for this hostname
                matching_records = []
                for record in dns_config:
                    # Each record is in format "IP hostname"
                    parts = record.split(' ', 1)
                    if len(parts) == 2 and parts[1] == host:
                        ip = parts[0]
                        matching_records.append({"record": record, "ip": ip})
                
                if not matching_records:
                    continue
                
                record_found = True
                
                # Add all matching records to planned deletions
                for record_info in matching_records:
                    all_planned.append({
                        "pihole": target, 
                        "record": record_info["record"],
                        "ip": record_info["ip"],
                        "host": host
                    })
                
                # Handle actual deletion (confirm=true)
                if confirm:
                    for record_info in matching_records:
                        ip = record_info["ip"]
                        client.config.remove_local_a_record(host, ip)
                        all_deleted.append({
                            "pihole": target, 
                            "record": record_info["record"],
                            "ip": ip,
                            "host": host
                        })
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error processing Pi-hole '{target}': {str(e)}"
                }
        
        # Return appropriate response based on results
        if not record_found:
            return {
                "status": "not_found",
                "message": f"No A records for '{host}' exist in any selected Pi-hole; nothing to delete"
            }
        
        if not confirm:
            return {
                "status": "pending_deletion",
                "planned": all_planned,
                "message": f"Call again with confirm=true to delete {len(all_planned)} record(s) from {len(set(r['pihole'] for r in all_planned))} Pi-hole(s)"
            }
        
        return {
            "status": "deleted",
            "deleted": all_deleted,
            "message": f"Removed {len(all_deleted)} record(s) from {len(set(r['pihole'] for r in all_deleted))} Pi-hole(s)"
        }
    
    @mcp.tool(name="remove_local_cname_record", description="Remove a local CNAME record from Pi-hole with confirmation")
    def remove_local_cname_record(host: str, confirm: bool = False, pihole: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a local CNAME record from Pi-hole with confirmation
        
        This requires a two-step process for safety:
        1. First call with confirm=false (default) returns what would be deleted
        2. Second call with confirm=true performs the actual deletion
        
        Args:
            host: The hostname for this CNAME record (required)
            confirm: Set to true to confirm deletion, false for preview only
            pihole: Optional Pi-hole name to target. If None, apply to all configured Pi-holes.
        
        Returns:
            Dict with status ("not_found", "pending_deletion", "deleted", or "error"),
            message, and planned/deleted entries
        """
        # Determine which Pi-holes to target
        targets = [pihole] if pihole is not None else pihole_clients.keys()
        
        # Check if specified pihole exists
        if pihole is not None and pihole not in pihole_clients:
            return {
                "status": "error",
                "message": f"Pi-hole '{pihole}' not found"
            }
        
        all_planned = []
        all_deleted = []
        record_found = False
        
        # Process each target Pi-hole
        for target_pihole in targets:
            client = pihole_clients[target_pihole]
            
            try:
                # Get current CNAME records section
                response = client.config.get_config_section('dns/cnameRecords')
                # Extract cnameRecords from nested structure
                dns_config = response.get('config', {}).get('dns', {}).get('cnameRecords', [])
                
                # Find all records for this hostname
                matching_records = []
                for record in dns_config:
                    # Each record is in format "host,target,ttl"
                    parts = record.split(',')
                    if len(parts) >= 1 and parts[0] == host:
                        target = parts[1] if len(parts) > 1 else ""
                        ttl = int(parts[2]) if len(parts) > 2 else 300
                        matching_records.append({"record": record, "target": target, "ttl": ttl})
                
                if not matching_records:
                    continue
                
                record_found = True
                
                # Add all matching records to planned deletions
                for record_info in matching_records:
                    all_planned.append({
                        "pihole": target_pihole, 
                        "record": record_info["record"],
                        "host": host,
                        "target": record_info["target"],
                        "ttl": record_info["ttl"]
                    })
                
                # Handle actual deletion (confirm=true)
                if confirm:
                    for record_info in matching_records:
                        target = record_info["target"]
                        ttl = record_info["ttl"]
                        client.config.remove_local_cname(host, target, ttl)
                        all_deleted.append({
                            "pihole": target_pihole, 
                            "record": record_info["record"],
                            "host": host,
                            "target": target,
                            "ttl": ttl
                        })
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error processing Pi-hole '{target_pihole}': {str(e)}"
                }
        
        # Return appropriate response based on results
        if not record_found:
            return {
                "status": "not_found",
                "message": f"No CNAME records for '{host}' exist in any selected Pi-hole"
            }
        
        if not confirm:
            return {
                "status": "pending_deletion",
                "planned": all_planned,
                "message": f"Call again with confirm=true to delete {len(all_planned)} record(s) from {len(set(r['pihole'] for r in all_planned))} Pi-hole(s)"
            }
        
        return {
            "status": "deleted",
            "deleted": all_deleted,
            "message": f"Removed {len(all_deleted)} CNAME record(s) from {len(set(r['pihole'] for r in all_deleted))} Pi-hole(s)"
        } 