import unittest

from pihole6api.metrics import PiHole6Metrics
from tools.metrics import register_tools


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name, description):
        def decorator(func):
            self.tools[name] = func
            return func
        return decorator


class FakeConnection:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return {"queries": []}


class FakePiHoleClient:
    def __init__(self, connection):
        self.connection = connection
        self.metrics = PiHole6Metrics(connection)


class ListQueriesTests(unittest.TestCase):
    def test_client_filter_is_sent_as_client_ip(self):
        connection = FakeConnection()
        client = FakePiHoleClient(connection)
        mcp = FakeMCP()

        register_tools(mcp, {"pihole": client})

        mcp.tools["list_queries"](
            piholes=["pihole"],
            client_filter="192.168.1.3",
        )

        self.assertEqual(len(connection.calls), 1)

        path, params = connection.calls[0]

        self.assertEqual(path, "queries")
        self.assertEqual(params["client_ip"], "192.168.1.3")
        self.assertNotIn("client", params)

    def test_client_filter_preserves_other_query_parameters(self):
        connection = FakeConnection()
        client = FakePiHoleClient(connection)
        mcp = FakeMCP()

        register_tools(mcp, {"pihole": client})

        mcp.tools["list_queries"](
            piholes=["pihole"],
            length=42,
            from_ts=1000,
            until_ts=2000,
            upstream="1.1.1.1",
            domain="example.com",
            client_filter="192.168.1.3",
            cursor="next-page",
        )

        self.assertEqual(len(connection.calls), 1)

        path, params = connection.calls[0]

        self.assertEqual(path, "queries")
        self.assertEqual(
            params,
            {
                "length": 42,
                "from": 1000,
                "until": 2000,
                "upstream": "1.1.1.1",
                "domain": "example.com",
                "client_ip": "192.168.1.3",
                "cursor": "next-page",
            },
        )

    def test_without_client_filter_uses_existing_query_path(self):
        connection = FakeConnection()
        client = FakePiHoleClient(connection)
        mcp = FakeMCP()

        register_tools(mcp, {"pihole": client})

        mcp.tools["list_queries"](
            piholes=["pihole"],
            length=25,
            domain="example.org",
        )

        self.assertEqual(len(connection.calls), 1)

        path, params = connection.calls[0]

        self.assertEqual(path, "queries")
        self.assertEqual(params["length"], 25)
        self.assertEqual(params["domain"], "example.org")
        self.assertNotIn("client", params)
        self.assertNotIn("client_ip", params)


if __name__ == "__main__":
    unittest.main()
