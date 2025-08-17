import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, override

from agentle.agents.conversations.conversation_store import ConversationStore
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.messages.user_message import UserMessage


class JSONFileConversationStore(ConversationStore):
    """A conversation store that persists conversations to JSON files.
    
    Each conversation is stored as a separate JSON file in the specified directory.
    The filename format is: {chat_id}.json
    """
    
    _storage_dir: Path

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        message_limit: int | None = None,
        override_old_messages: bool | None = None,
    ) -> None:
        """Initialize the JSON file conversation store.
        
        Args:
            storage_dir: Directory where conversation JSON files will be stored. 
                        Defaults to './conversations' if not provided.
            message_limit: Maximum number of messages to store per conversation
            override_old_messages: Whether to remove old messages when limit is reached
        """
        super().__init__(message_limit, override_old_messages)
        if storage_dir is None:
            storage_dir = "./.conversations"
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, chat_id: str) -> Path:
        """Get the file path for a given chat ID."""
        # Sanitize chat_id to be filesystem-safe
        safe_chat_id = "".join(c for c in chat_id if c.isalnum() or c in ("-", "_", "."))
        return self._storage_dir / f"{safe_chat_id}.json"

    def _load_messages(self, chat_id: str) -> list[dict[str, Any]]:
        """Load messages from the JSON file for a given chat ID."""
        file_path = self._get_file_path(chat_id)
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_messages(self, chat_id: str, messages: list[dict[str, Any]]) -> None:
        """Save messages to the JSON file for a given chat ID."""
        file_path = self._get_file_path(chat_id)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
        except OSError:
            # Handle file write errors gracefully
            pass

    def _message_to_dict(self, message: DeveloperMessage | UserMessage | AssistantMessage) -> dict[str, Any]:
        """Convert a message object to a dictionary for JSON serialization."""
        message_dict = message.model_dump()
        # Add message type for proper deserialization
        message_dict["_message_type"] = type(message).__name__
        return message_dict

    def _dict_to_message(self, message_dict: dict[str, Any]) -> DeveloperMessage | UserMessage | AssistantMessage:
        """Convert a dictionary back to a message object."""
        message_type = message_dict.pop("_message_type", None)
        
        if message_type == "DeveloperMessage":
            return DeveloperMessage.model_validate(message_dict)
        elif message_type == "UserMessage":
            return UserMessage.model_validate(message_dict)
        elif message_type == "AssistantMessage":
            return AssistantMessage.model_validate(message_dict)
        else:
            # Fallback: try to determine type from content
            if "role" in message_dict:
                role = message_dict.get("role")
                if role == "developer":
                    return DeveloperMessage.model_validate(message_dict)
                elif role == "user":
                    return UserMessage.model_validate(message_dict)
                elif role == "assistant":
                    return AssistantMessage.model_validate(message_dict)
            
            # Default fallback to UserMessage
            return UserMessage.model_validate(message_dict)

    @override
    async def add_message_async(
        self, chat_id: str, message: DeveloperMessage | UserMessage | AssistantMessage
    ) -> None:
        """Add a message to the conversation."""
        messages_data = self._load_messages(chat_id)
        
        # Apply message limit logic
        if self.message_limit is not None:
            if len(messages_data) >= self.message_limit:
                if self.override_old_messages:
                    # Remove oldest messages to make room
                    messages_to_remove = len(messages_data) - self.message_limit + 1
                    messages_data = messages_data[messages_to_remove:]
                else:
                    # Don't add message if limit reached and not overriding
                    return
        
        # Add the new message
        message_dict = self._message_to_dict(message)
        messages_data.append(message_dict)
        
        # Save to file
        self._save_messages(chat_id, messages_data)

    @override
    async def get_conversation_history_async(
        self, chat_id: str
    ) -> Sequence[DeveloperMessage | UserMessage | AssistantMessage]:
        """Get the conversation history for a given chat ID."""
        messages_data = self._load_messages(chat_id)
        
        # Convert dictionaries back to message objects
        messages = []
        for message_dict in messages_data:
            try:
                message = self._dict_to_message(message_dict.copy())
                messages.append(message)
            except Exception:
                # Skip malformed messages
                continue
        
        return messages

    @override
    async def clear_conversation_async(self, chat_id: str) -> None:
        """Clear the conversation history for a given chat ID."""
        file_path = self._get_file_path(chat_id)
        
        try:
            if file_path.exists():
                os.remove(file_path)
        except OSError:
            # Handle file deletion errors gracefully
            pass