from app.config import get_llm
from app.tools.file_tools import (
    search_files,
    read_file
)


def create_tool_agent():

    llm = get_llm()

    tools = [
        search_files,
        read_file
    ]

    return llm.bind_tools(tools)