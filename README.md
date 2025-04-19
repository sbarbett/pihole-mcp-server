# pihole-mcp-serer

A Model Context Protocol (MCP) server for Pi-hole. This server exposes Pi-hole functionality as tools that can be used by AI assistants.

## Features

- **ListLocalDNS**: Returns all local DNS settings from Pi-hole
- **ListQueries**: Returns recent DNS query history from Pi-hole
- **Multiple Pi-hole Support**: Manage up to 4 Pi-holes from a single MCP server
- _...more to come..._

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

## Docker Deployment

Run the Pi-hole MCP server in Docker.

### Using Docker Compose

1. Pull and start the container:
   ```
   docker-compose up -d
   ```

2. The server will be available at `http://localhost:8383`

### Manual Docker Build

Alternatively, you can build and run the Docker container manually:

```
docker build -t pihole-mcp .
docker run -p 8383:8000 --env-file .env -d pihole-mcp
```

## Run Locally

The Docker deployment uses SSE mode for two-way communication between the host and container. You could (theoretically) use STDIO mode with Docker exec. If you want to run it locally, though, you can simply run it with `uv`. This is particularly useful for quickly inspecting tools and resources with the inbuilt `mcp` dev utilities. For example:

```
uv run mcp dev main.py
```

Then in your web browser navigate to `http://localhost:6274`.

## API

This MCP server exposes the following resources and tools:

### Resources

- `piholes://`: Returns information about all configured Pi-holes

### Tools

- `list_local_dns`: Lists all local DNS settings from Pi-hole(s)
- `list_queries`: Fetches the recent DNS query history from Pi-hole(s)

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