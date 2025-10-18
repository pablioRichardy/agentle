from typing import Optional, Any, Literal
import uuid
from rsb.models.base_model import BaseModel
from rsb.models.field import Field
import time


class Assistant(BaseModel):
    created_at: int = Field(
        default=int(time.time()),
        description="""The time the assistant was created.""",
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="""The ID of the assistant.""",
    )

    model: str = Field(
        ...,
        description="""ID of the model to use. You can use the List models API
    to see all of your available models, or see our Model
    overview for descriptions of them.""",
    )

    description: Optional[str] = Field(
        default=None,
        description="""The description of the assistant. The maximum
        length is 512 characters.""",
    )

    instructions: Optional[str] = Field(
        default=None,
        description="""The system instructions that the assistant uses. The maximum length is 256,000 characters.""",
    )

    metadata: Optional[dict[str, str]] = Field(
        default=None,
        description="""Set of 16 key-value pairs that can be attached to an object. 
        This can be useful for storing additional information about the object in a 
        structured format, and querying for objects via API or the dashboard. 
        Keys are strings with a maximum length of 64 characters. 
        Values are strings with a maximum length of 512 characters.""",
    )

    name: Optional[str] = Field(
        default=None,
        description="""The name of the assistant. The maximum length is 256 characters.""",
    )

    reasoning_effort: Optional[Literal["minimal", "low", "medium", "high"]] = Field(
        default="medium",
        description="""Constrains effort on reasoning for reasoning models. 
        Currently supported values are minimal, low, medium, and high. 
        Reducing reasoning effort can result in faster responses and fewer tokens 
        used on reasoning in a response. 
        Note: The gpt-5-pro model defaults to (and only supports) high reasoning effort.""",
    )

    response_format: Optional[str | dict[str, Any]] = Field(
        default="auto",
        description="""Specifies the format that the model must output. 
        Compatible with GPT-4o, GPT-4 Turbo, and all GPT-3.5 Turbo models since gpt-3.5-turbo-1106.
        
        Setting to { "type": "json_schema", "json_schema": {...} } enables Structured Outputs 
        which ensures the model will match your supplied JSON schema.
        
        Setting to { "type": "json_object" } enables JSON mode, which ensures the message 
        the model generates is valid JSON.
        
        Important: when using JSON mode, you must also instruct the model to produce JSON 
        yourself via a system or user message. Without this, the model may generate an 
        unending stream of whitespace until the generation reaches the token limit.""",
    )

    temperature: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="""What sampling temperature to use, between 0 and 2. 
        Higher values like 0.8 will make the output more random, while lower values 
        like 0.2 will make it more focused and deterministic.""",
    )

    tool_resources: Optional[dict[str, Any]] = Field(
        default=None,
        description="""A set of resources that are used by the assistant's tools. 
        The resources are specific to the type of tool. For example, the code_interpreter 
        tool requires a list of file IDs, while the file_search tool requires a list of 
        vector store IDs.""",
    )

    tools: Optional[list[dict[str, Any]]] = Field(
        default_factory=list,
        description="""A list of tool enabled on the assistant. There can be a maximum 
        of 128 tools per assistant. Tools can be of types code_interpreter, file_search, 
        or function.""",
    )

    top_p: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="""An alternative to sampling with temperature, called nucleus sampling, 
        where the model considers the results of the tokens with top_p probability mass. 
        So 0.1 means only the tokens comprising the top 10% probability mass are considered.
        
        We generally recommend altering this or temperature but not both.""",
    )