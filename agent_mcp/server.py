from fastmcp import FastMCP
from agent_mcp.tools import setup_tools
from agent_mcp.resources import setup_memory_and_rag_tools

mcp = FastMCP("ObsidianaMCP")

setup_memory_and_rag_tools(mcp=mcp)
setup_tools(mcp=mcp)

if __name__ == "__main__":
    mcp.run()