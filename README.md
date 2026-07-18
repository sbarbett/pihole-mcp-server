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

# Unbound resolver(s) behind Pi-hole (optional — enables the unbound_* tools).
# Requires Unbound remote-control over TLS (see "Unbound remote control" below).
#UNBOUND_HOST=192.168.1.2
#UNBOUND_PORT=8953                 # optional, default 8953
#UNBOUND_NAME=dns01                # optional, defaults to host
#UNBOUND_CONTROL_CERT=/certs/unbound_control.pem
#UNBOUND_CONTROL_KEY=/certs/unbound_control.key
#UNBOUND_SERVER_CERT=/certs/unbound_server.pem
# Additional resolvers (up to 4): UNBOUND2_*, UNBOUND3_*, UNBOUND4_*
# (cert paths fall back to the primary's when omitted)
#UNBOUND2_HOST=192.168.1.3
#UNBOUND2_NAME=dns02
```

## Project Structure

The project follows a modular organization for better maintainability:

```
/
├── main.py                # Main application entry point
├── tools/                 # Pi-hole tools organized by functionality
│   ├── __init__.py
│   ├── config.py          # Configuration-related tools (DNS settings)
│   ├── metrics.py         # Metrics and query-related tools
│   ├── blocking.py        # Blocking, adlist, and allow/deny domain-rule tools
│   └── unbound.py         # Unbound recursive-resolver control tools (optional)
├── resources/             # MCP resources
│   ├── __init__.py
│   └── common.py          # Common resources (piholes://, version://)
├── docker-compose.yml     # Docker Compose configuration for production
├── docker-compose.dev.yml # Docker Compose for development with volume mounts
└── Dockerfile             # Docker build configuration
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

#### Configuration

- `list_local_dns`: Lists all local DNS settings from Pi-hole(s)
- `add_local_a_record`: Adds a local A record to Pi-hole(s).
- `add_local_cname_record`: Adds a local CNAME record to Pi-hole(s).
- `remove_local_a_record`: Removes all A records for a hostname.
- `remove_local_cname_record`: Removes all CNAME records for a hostname.

#### Metrics

- `list_queries`: Fetches the recent DNS query history from Pi-hole(s)
- `list_query_suggestions`: Get query filter suggestions
- `list_query_history`: Get activity graph data for queries over time

#### Blocking

- `get_blocking_status`: Get ad-blocking status (enabled/disabled and any timer)
- `set_blocking`: Enable/disable ad-blocking, optionally for a number of seconds
- `list_blocklists`: List adlists (`block` or `allow`)
- `add_blocklist`: Add an adlist by URL
- `remove_blocklist`: Remove an adlist by URL
- `update_gravity`: Rebuild blocklists (apply adlist changes)
- `add_domain_rule`: Add an allow/deny domain rule (`exact` or `regex`)
- `remove_domain_rule`: Remove an allow/deny domain rule
- `get_domain_rule`: Look up an allow/deny domain rule

#### Unbound

Controls the Unbound recursive resolver(s) behind Pi-hole over Unbound's
remote-control interface (see [Unbound remote control](#unbound-remote-control)).
Enabled when `UNBOUND_HOST` is set. Each result is `{"unbound": name, "ok": bool, ...}`.

- `unbound_status`: Resolver status (version, threads, uptime, modules)
- `unbound_stats`: Resolver statistics (queries, cache hits/misses, recursion times)
- `unbound_flush_domain`: Flush a single domain from the resolver cache
- `unbound_flush_zone`: Flush a zone (pass `.` for the whole cache)
- `unbound_reload`: Reload config and flush the cache
- `unbound_list_local_zones` / `unbound_list_local_data`: List resolver-level overrides
- `unbound_add_local_data` / `unbound_remove_local_data`: Manage resolver-level DNS overrides
- `unbound_list_forwards`: List forward-zones

## Unbound remote control

The `unbound_*` tools connect to Unbound's remote-control interface over TLS.
Enable it in `unbound.conf`:

```
remote-control:
    control-enable: yes
    control-interface: 127.0.0.1        # keep a local interface for unbound-control
    control-interface: 0.0.0.0          # or a specific LAN IP this server can reach
    control-port: 8953
    control-use-cert: yes
```

> **Important:** do not keep a UNIX-socket `control-interface` (a path such as
> `/run/unbound.ctl`) alongside the TCP interface. If *any* control-interface is
> a UNIX socket, Unbound runs the entire control facility **without TLS**
> (`unbound-control status` reports `control(namedpipe)`) and the TCP port
> answers in plaintext, so TLS handshakes are refused. Use IP-address interfaces
> only — add `127.0.0.1` so local `unbound-control` keeps working — and confirm
> `unbound-control status` reports `control(ssl)`.

Run `unbound-control-setup` once to generate `unbound_server.pem`,
`unbound_control.pem` and `unbound_control.key` in Unbound's directory and
restart Unbound. Copy those three files to wherever this server runs and point
the `UNBOUND_*` env vars at them.

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