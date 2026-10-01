import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def verify_protocol(command, required_tools):
    async with asyncio.timeout(30):
        async with stdio_client(StdioServerParameters(command=command)) as streams:
            async with ClientSession(*streams) as session:
                initialization = await session.initialize()
                assert initialization.serverInfo.name
                tools = (await session.list_tools()).tools
                tools_by_name = {tool.name: tool for tool in tools}
                assert len(tools_by_name) == len(tools)
                assert set(required_tools) <= tools_by_name.keys()
                for tool in tools:
                    assert tool.inputSchema["type"] == "object", tool.name
                assert "run_script" not in tools_by_name
                print(f"MCP handshake verified: {len(tools)} tools")


if __name__ == "__main__":
    asyncio.run(verify_protocol(sys.argv[1], sys.argv[2:]))
