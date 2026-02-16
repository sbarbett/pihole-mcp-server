# 🍓 pihole-mcp-serer

A Model Context Protocol (MCP) server for Pi-hole. This server exposes Pi-hole functionality as tools that can be used by AI assistants.

## Dependencies

### Docker

- [Docker install guide](https://docs.docker.com/engine/install/)

### `uv` (Optional, for Development)

If you want to run the application locally, use `uv`. Install it with your package manager of choice.

## Environment

Create a `.env` file in the project root with your Pi-hole credentials:

```
# Primary Pi-hole (required)
PIHOLE_URL=https://your-pihole.local/
PIHOLE_PASSWORD=your-admin-password
#PIHOLE_NAME=Primary        # optional, defaults to URL if unset

# Secondary Pi-hole (optional)
#PIHOLE2_URL=https://secondary-pihole.local/
#PIHOLE2_PASSWORD=password2
#PIHOLE2_NAME=Secondary     # optional

# Up to 4 Pi-holes:
#PIHOLE3_URL=...
#PIHOLE3_PASSWORD=...
#PIHOLE3_NAME=...

#PIHOLE4_URL=...
#PIHOLE4_PASSWORD=...
#PIHOLE4_NAME=...
```

## Project Structure

The project follows a modular organization for better maintainability:

```
/
├── main.py                  # Main application entry point
├── tools/                   # Pi-hole tools organized by functionality
│   ├── __init__.py
│   ├── confirmation.py      # Shared confirmation token utilities
│   ├── config.py            # Configuration & local DNS record tools
│   ├── metrics.py           # Query logs, statistics, and analytics tools
│   ├── dns_control.py       # DNS blocking status control
│   ├── dhcp.py              # DHCP lease management
│   ├── groups.py            # Group management
│   ├── domains.py           # Domain allow/deny list management
│   ├── lists.py             # Blocklist/allowlist management
│   ├── clients.py           # Client/device management
│   ├── system.py            # System info, diagnostics, logs, and actions
│   └── network.py           # Network device discovery and configuration
├── resources/               # MCP resources
│   ├── __init__.py
│   ├── common.py            # Common resources (piholes://, version://)
│   └── discovery.py         # Tool discovery resources (list-tools://)
├── prompts/                 # MCP prompts
│   ├── __init__.py
│   └── guide.py             # LLM instruction guide
├── docker-compose.yml       # Docker Compose configuration for production
├── docker-compose.dev.yml   # Docker Compose for development with volume mounts
└── Dockerfile               # Docker build configuration
```

This structure separates the code into logical components while maintaining compatibility with all run modes.

## Running the Server

There are several ways to run the Pi-hole MCP server:

### Using Docker (Recommended for Production)

```bash
# Standard deployment
docker-compose up -d
```

The server will be available at `http://localhost:8383`

### Development Mode with Docker

For development, use the dev compose file which builds locally:

```bash
docker-compose -f docker-compose.dev.yml up
```

### MCP Inspector

You can run the MCP inspector using `uv` and the `mcp` CLI:

```bash
uv run mcp dev main.py
```

This will start an interactive interface at `http://localhost:6274` where you can test tools and resources.

## API

This MCP server exposes the following resources and tools:

### Resources

- `piholes://`: Returns information about all configured Pi-holes
- `version://`: Returns the MCP server version
- `list-tools://`: Returns a list of tool categories
  - `list-tools://{category}`: Returns a list of tools within a specific category

### Tools

Each tool call returns results as a list of dictionaries with the following structure:
```
[
  {
    "pihole": "Pi-hole Name",
    "data": [...]  # Result data from this Pi-hole
  },
  ...
]
```

All destructive operations (deletions) use a two-step confirmation token process: the first call returns a preview and a token, and the second call with the token performs the actual deletion.

#### DNS Control

- `get_blocking_status`: Get the current DNS blocking status
- `set_blocking_status`: Enable or disable DNS blocking (with optional timer)

#### Configuration & Local DNS

- `list_local_dns`: Lists all local DNS settings from Pi-hole(s)
- `add_local_a_record`: Adds a local A record to Pi-hole(s)
- `add_local_cname_record`: Adds a local CNAME record to Pi-hole(s)
- `remove_local_a_record`: Removes all A records for a hostname (with confirmation)
- `remove_local_cname_record`: Removes all CNAME records for a hostname (with confirmation)
- `get_config`: Get Pi-hole configuration settings (full or by section)
- `update_config`: Update Pi-hole configuration settings

#### Metrics & Statistics

- `list_queries`: Fetches the recent DNS query history with filtering
- `list_query_suggestions`: Get query filter suggestions
- `list_query_history`: Get activity graph data for queries over time
- `get_stats_summary`: Get activity overview (total queries, blocked, percentage, etc.)
- `get_top_domains`: Get top queried or blocked domains
- `get_top_clients`: Get top DNS query clients
- `get_stats_upstreams`: Get upstream DNS server statistics
- `get_query_types`: Get DNS query type distribution (A, AAAA, PTR, etc.)
- `get_recent_blocked`: Get recently blocked domains
- `get_history_clients`: Get per-client activity history over time
- `get_database_stats`: Get long-term database statistics for a time range

#### DHCP

- `get_dhcp_leases`: Get active DHCP leases
- `remove_dhcp_lease`: Remove a DHCP lease by IP address

#### Group Management

- `get_groups`: Get all groups
- `add_group`: Add a new group
- `update_group`: Update an existing group
- `delete_group`: Delete a group (with confirmation)

#### Domain Management (Allow/Deny)

- `get_domains`: Get all allow/deny domain entries
- `add_domain`: Add a domain to the allow or deny list (exact or regex)
- `update_domain`: Update an existing domain entry
- `delete_domain`: Delete a domain entry (with confirmation)

#### List Management (Blocklists/Allowlists)

- `get_lists`: Get all blocklists and allowlists
- `add_list`: Add a blocklist or allowlist URL
- `update_list`: Update an existing list entry
- `delete_list`: Delete a list entry (with confirmation)
- `search_list`: Search for a domain across all lists

#### Client Management

- `get_clients`: Get all configured clients
- `get_client_suggestions`: Get suggested clients from known network devices
- `add_client`: Add a client for group-based management
- `update_client`: Update an existing client entry
- `delete_client`: Delete a client (with confirmation)

#### System Info & Actions

- `get_system_info`: Get comprehensive system information (version, host, FTL, sensors, metrics)
- `get_pihole_version`: Get Pi-hole version details
- `get_padd_summary`: Get PADD-style dashboard summary
- `get_diagnosis_messages`: Get diagnostic/warning messages
- `get_database_info`: Get long-term database statistics
- `get_logs`: Get Pi-hole logs (dnsmasq, FTL, or webserver)
- `run_gravity`: Re-download and process all blocklists
- `restart_dns`: Restart the FTL DNS resolver
- `flush_arp`: Flush the network table (ARP cache)
- `flush_logs`: Flush DNS query logs

#### Network

- `get_network_devices`: Get network devices discovered by Pi-hole
- `delete_network_device`: Remove a device from the network table
- `get_network_info`: Get gateway, interfaces, and routes

## Testing in `goose`

Goose is a CLI LLM client that's useful for testing and development. Follow their install instructions [here](https://block.github.io/goose/docs/quickstart/).

The following assumes you've completed the initial setup with `goose configure`.

### Configure Extension

1. Type `goose configure` to open the configuration menu.
2. Select **Add Extension**
3. Select **Remote Extension**
4. It will ask for a name. It doesn't matter what you name it. I called mine `pihole-mcp`.
5. When it asks _"What is the SSE endpoint URI?"_ enter `http://localhost:8383/sse`.
6. Enter a timeout.
7. Add a description if you'd like.
8. Select **No** when it asks about environment variables.
   ![Screenshot of configuration](./img/configure-goose-2.jpg)

### Start a Session

Once the server is installed, start a chat session.

```sh
goose session
```

Try asking it: _"What are my local DNS records?"_

![Screenshot of local DNS tool](./img/local-dns-2.jpg)

...or telling it: _"Show me my recent DNS queries."_

![Screenshot of queries](./img/recent-queries.jpg)

## Claude Desktop

Claude's desktop client currently only support's the STDIO protocol, however you can use a proxy to communicate with the SSE endpoint.

Add the following to your `claude_desktop_config.json` file.

```json
{
  "mcpServers": {
    "pihole": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8383/sse"
      ]
    }
  }
}
```

If you're connecting to a different host on your local network and using an unsecured connection, you'll need to explicitly allow it with the `--allow-http` argument. For example:

```json
{
  "mcpServers": {
    "pihole": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://192.168.1.255:8383/sse",
        "--allow-http"
      ]
    }
  }
}
```

Afterwards, completely restart the application and try it out.

![Claude DNS info](./img/claude-dns.png)

![Claude query info](./img/claude-query.png)

## License

[MIT](./LICENSE)