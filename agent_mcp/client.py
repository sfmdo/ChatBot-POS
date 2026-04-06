from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

class MCPClientManager:
    def __init__(self):
        self.stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def start(self):
        """Inicia el subproceso del servidor MCP usando uv y mantiene la sesión abierta."""
        server_params = StdioServerParameters(
            command="uv", 
            args=["run", "python", "-m", "agent_mcp.server"]
        )
        
        transport = await self.stack.enter_async_context(stdio_client(server_params))
        read, write = transport
        
        self.session = await self.stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

    async def stop(self):
        """Cierra el servidor cuando el bot se apaga."""
        await self.stack.aclose()

mcp_manager = MCPClientManager()