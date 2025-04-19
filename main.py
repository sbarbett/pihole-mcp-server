from mcp.server.fastmcp import FastMCP
from pihole6api import PiHole6Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Pi-hole client
url = os.getenv("PIHOLE_URL")
password = os.getenv("PIHOLE_PASSWORD")
client = PiHole6Client(url, password)

# Create MCP server
mcp = FastMCP("PiHoleMCP", version="0.1.0")


@mcp.tool(name="list_local_dns", description="List local A and CNAME records from Pi-hole")
def list_local_dns() -> list[dict]:
    """List all local DNS records (A and CNAME) from Pi-hole"""
    return client.config.get_config_section('dns')


@mcp.tool(name="list_queries", description="Fetch recent DNS query history")
def list_queries() -> list[dict]:
    """Fetch the recent DNS query history from Pi-hole"""
    return client.metrics.get_queries()


def main():
    print("Starting Pi-hole MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
