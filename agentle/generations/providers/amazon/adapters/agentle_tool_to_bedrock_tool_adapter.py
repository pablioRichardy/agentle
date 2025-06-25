from typing import override
from rsb.adapters.adapter import Adapter

from agentle.generations.tools.tool import Tool
from agentle.generations.providers.amazon.models.tool import Tool as BedrockTool


class AgentleToolToBedrockToolAdapter(Adapter[Tool, BedrockTool]):
    @override
    def adapt(self, _f: Tool) -> BedrockTool:
        return super().adapt(_f)
