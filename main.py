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
import logging

# Import modular components
from tools import config, metrics
from resources import common, discovery
from prompts import guide

# Setup logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pihole-mcp")

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
        return "0.0.0"

# Create MCP server
mcp = FastMCP(
    "PiHoleMCP", 
    version=get_version(),
    instructions="You are a helpful assistant that can help with Pi-hole network management tasks."
)

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
    
    logger.info("Closing Pi-hole client sessions...")
    for name, client in pihole_clients.items():
        try:
            client.close_session()
            logger.info(f"Successfully closed session for Pi-hole: {name}")
        except Exception as e:
            logger.error(f"Error closing session for Pi-hole {name}: {e}")
    
    sessions_closed = True


# Register cleanup handlers
atexit.register(close_pihole_sessions)

def signal_handler(sig, frame):
    logger.info("Received shutdown signal, cleaning up...")
    close_pihole_sessions()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register resources, tools, and prompts
common.register_resources(mcp, pihole_clients, get_version)
discovery.register_resources(mcp)
config.register_tools(mcp, pihole_clients)
metrics.register_tools(mcp, pihole_clients)
guide.register_prompt(mcp)

def main():
    logger.info("Starting Pi-hole MCP server...")
    mcp.run()

# Expose the MCP server over HTTP/SSE
app = mcp.sse_app()

if __name__ == "__main__":
    # Serve on 0.0.0.0:8000 so all LAN clients can connect
    uvicorn.run(app, host="0.0.0.0", port=8000)