from mcp.server.fastmcp import FastMCP
from pihole6api import PiHole6Client
import os
import tomli
from dotenv import load_dotenv
import uvicorn
from typing import List, Dict, Optional, Any
from pathlib import Path
import atexit
import signal
import sys

# Load environment variables from .env file
load_dotenv()

# Get version from pyproject.toml
def get_version() -> str:
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
            return pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError, tomli.TOMLDecodeError):
        # Fallback version if we can't read from pyproject.toml
        return "0.1.0"

# Create MCP server
mcp = FastMCP("PiHoleMCP", version=get_version())

# Initialize Pi-hole clients based on environment variables
pihole_clients = {}

# Initialize primary Pi-hole (required)
primary_url = os.getenv("PIHOLE_URL")
primary_password = os.getenv("PIHOLE_PASSWORD")
primary_name = os.getenv("PIHOLE_NAME", primary_url)

if not primary_url or not primary_password:
    raise ValueError("Primary Pi-hole configuration (PIHOLE_URL and PIHOLE_PASSWORD) is required")

pihole_clients[primary_name] = PiHole6Client(primary_url, primary_password)

# Initialize optional Pi-holes (2-4)
for i in range(2, 5):
    url = os.getenv(f"PIHOLE{i}_URL")
    if url:
        password = os.getenv(f"PIHOLE{i}_PASSWORD")
        name = os.getenv(f"PIHOLE{i}_NAME", url)
        pihole_clients[name] = PiHole6Client(url, password)


# Flag to track if sessions have been closed
sessions_closed = False

# Function to close all Pi-hole client sessions
def close_pihole_sessions():
    global sessions_closed
    
    # Avoid closing sessions more than once
    if sessions_closed:
        return
    
    print("Closing Pi-hole client sessions...")
    for name, client in pihole_clients.items():
        try:
            client.close_session()
            print(f"Successfully closed session for Pi-hole: {name}")
        except Exception as e:
            print(f"Error closing session for Pi-hole {name}: {e}")
    
    sessions_closed = True


# Register cleanup handlers
atexit.register(close_pihole_sessions)

def signal_handler(sig, frame):
    print("Received shutdown signal, cleaning up...")
    close_pihole_sessions()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@mcp.resource("piholes://")
def all_piholes() -> Dict[str, List[Dict[str, str]]]:
    """Return information about all configured Pi-holes"""
    piholes_list = [{"name": name, "url": client.connection.base_url} for name, client in pihole_clients.items()]
    return {"piholes": piholes_list}


@mcp.resource("version://")
def server_version() -> Dict[str, str]:
    """Return the current version of the Pi-hole MCP server"""
    return {"version": get_version()}


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


@mcp.tool(name="list_queries", description="Fetch recent DNS query history with filtering options")
def list_queries(
    piholes: Optional[List[str]] = None,
    length: int = 100,
    from_ts: Optional[int] = None,
    until_ts: Optional[int] = None,
    upstream: Optional[str] = None,
    domain: Optional[str] = None,
    client_filter: Optional[str] = None,
    cursor: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch the recent DNS query history from Pi-hole with filtering options
    
    Args:
        piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
        length: Number of queries to retrieve (default: 100)
        from_ts: Unix timestamp to filter queries from this time onward
        until_ts: Unix timestamp to filter queries up to this time
        upstream: Filter queries sent to a specific upstream destination
        domain: Filter queries for specific domains, supports wildcards (*)
        client_filter: Filter queries originating from a specific client
        cursor: Cursor for pagination to fetch the next chunk of results
    """
    result = []
    
    # Determine which Pi-holes to query
    targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
    
    for name in targets:
        client = pihole_clients[name]
        try:
            data = client.metrics.get_queries(
                length=length,
                from_ts=from_ts,
                until_ts=until_ts,
                upstream=upstream,
                domain=domain,
                client=client_filter,  # Use client_filter to avoid name conflict with client variable
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
    result = []
    
    # Determine which Pi-holes to query
    targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
    
    for name in targets:
        client = pihole_clients[name]
        try:
            data = client.metrics.get_query_suggestions()
            result.append({"pihole": name, "data": data})
        except Exception as e:
            result.append({"pihole": name, "error": str(e)})
    
    return result


@mcp.tool(name="list_query_history", description="Get activity graph data for Pi-hole queries over time")
def list_query_history(piholes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get activity graph data showing the distribution of queries over time
    
    This data is used to generate the total queries over time graph in the Pi-hole dashboard.
    The sum of the values in the individual data arrays may be smaller than the total number
    of queries for the corresponding timestamp. The remaining queries are ones that do not fit
    into the shown categories (e.g. database busy, unknown status queries, etc.).
    
    Args:
        piholes: Optional list of Pi-hole names to query. If None, query all configured Pi-holes.
    
    Returns:
        List of dictionaries containing activity graph data for each Pi-hole
    """
    result = []
    
    # Determine which Pi-holes to query
    targets = pihole_clients.keys() if piholes is None else [p for p in piholes if p in pihole_clients]
    
    for name in targets:
        client = pihole_clients[name]
        try:
            data = client.metrics.get_history()
            result.append({"pihole": name, "data": data})
        except Exception as e:
            result.append({"pihole": name, "error": str(e)})
    
    return result


def main():
    print("Starting Pi-hole MCP server...")
    mcp.run()

# Expose the MCP server over HTTP/SSE
app = mcp.sse_app()

if __name__ == "__main__":
    # Serve on 0.0.0.0:8000 so all LAN clients can connect
    uvicorn.run(app, host="0.0.0.0", port=8000)