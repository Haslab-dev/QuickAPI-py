"""
QuickAPI Chat Memory Module

In-memory conversation management for chat applications.
"""

import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


class ChatMemory:
    """
    In-memory chat conversation management.
    
    Provides functionality to store, retrieve, and manage chat messages
    with conversation history and context window management.
    """
    
    def __init__(self, max_messages: int = 100, max_context: int = 10):
        """
        Initialize chat memory.
        
        Args:
            max_messages: Maximum number of messages to store
            max_context: Maximum number of messages to include in context
        """
        self.messages: List[ChatMessage] = []
        self.max_messages = max_messages
        self.max_context = max_context
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """
        Add a message to the conversation.
        
        Args:
            role: Message role (user, assistant, system, etc.)
            content: Message content
            metadata: Optional metadata
            
        Returns:
            The created message
        """
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        
        # Trim if exceeding max messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        return message
    
    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """
        Get messages from the conversation.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit > 0 else []
    
    def get_context(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM context.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            List of message dictionaries for LLM
        """
        # Get recent messages for context
        context_messages = self.get_messages(self.max_context)
        
        # Filter and format
        formatted_messages = []
        for msg in context_messages:
            if msg.role == "system" and not include_system:
                continue
            
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted_messages
    
    def get_last_message(self, role: Optional[str] = None) -> Optional[ChatMessage]:
        """
        Get the last message, optionally filtered by role.
        
        Args:
            role: Optional role to filter by
            
        Returns:
            The last message or None
        """
        if not self.messages:
            return None
        
        if role is None:
            return self.messages[-1]
        
        # Find last message with specified role
        for msg in reversed(self.messages):
            if msg.role == role:
                return msg
        
        return None
    
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        logger.info("Chat memory cleared")
    
    def trim_to_last(self, n: int):
        """
        Keep only the last n messages.
        
        Args:
            n: Number of messages to keep
        """
        if n >= 0:
            self.messages = self.messages[-n:]
        else:
            self.messages.clear()
        
        logger.info(f"Chat memory trimmed to last {n} messages")
    
    def remove_messages(self, indices: List[int]):
        """
        Remove messages by indices.
        
        Args:
            indices: List of indices to remove
        """
        # Sort indices in descending order to avoid shifting
        sorted_indices = sorted(indices, reverse=True)
        
        for idx in sorted_indices:
            if 0 <= idx < len(self.messages):
                del self.messages[idx]
        
        logger.info(f"Removed {len(indices)} messages from chat memory")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation.
        
        Returns:
            Dictionary with conversation statistics
        """
        if not self.messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "system_messages": 0
            }
        
        user_count = sum(1 for msg in self.messages if msg.role == "user")
        assistant_count = sum(1 for msg in self.messages if msg.role == "assistant")
        system_count = sum(1 for msg in self.messages if msg.role == "system")
        
        # Get time range
        timestamps = [msg.timestamp for msg in self.messages]
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration = end_time - start_time
        
        return {
            "total_messages": len(self.messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "system_messages": system_count,
            "duration_seconds": duration,
            "start_time": start_time,
            "end_time": end_time
        }
    
    def export_conversation(self, format: str = "dict") -> Any:
        """
        Export the conversation in various formats.
        
        Args:
            format: Export format ("dict", "json", "txt")
            
        Returns:
            Exported conversation data
        """
        if format == "dict":
            return [msg.to_dict() for msg in self.messages]
        
        elif format == "json":
            import json
            return json.dumps([msg.to_dict() for msg in self.messages], indent=2)
        
        elif format == "txt":
            lines = []
            for msg in self.messages:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg.timestamp))
                lines.append(f"[{timestamp}] {msg.role}: {msg.content}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def load_conversation(self, data: Any, format: str = "dict"):
        """
        Load conversation data from various formats.
        
        Args:
            data: Conversation data
            format: Data format ("dict", "json", "txt")
        """
        self.clear()
        
        if format == "dict":
            for msg_data in data:
                self.messages.append(ChatMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data.get("timestamp", time.time()),
                    metadata=msg_data.get("metadata", {})
                ))
        
        elif format == "json":
            import json
            msg_data = json.loads(data)
            self.load_conversation(msg_data, "dict")
        
        elif format == "txt":
            lines = data.split("\n")
            for line in lines:
                if line.strip():
                    # Parse format: [timestamp] role: content
                    try:
                        if line.startswith("[") and "] " in line:
                            timestamp_part, rest = line.split("] ", 1)
                            role_content = rest.split(": ", 1)
                            if len(role_content) == 2:
                                role, content = role_content
                                self.add_message(role, content)
                    except:
                        # Fallback: treat entire line as content
                        self.add_message("user", line)
        
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        logger.info(f"Loaded {len(self.messages)} messages from {format} format")
    
    def search_messages(self, query: str, role: Optional[str] = None) -> List[ChatMessage]:
        """
        Search messages by content.
        
        Args:
            query: Search query
            role: Optional role to filter by
            
        Returns:
            List of matching messages
        """
        query_lower = query.lower()
        matching_messages = []
        
        for msg in self.messages:
            if role and msg.role != role:
                continue
            
            if query_lower in msg.content.lower():
                matching_messages.append(msg)
        
        return matching_messages
    
    def get_token_count_estimate(self) -> int:
        """
        Estimate total token count of the conversation.
        
        Returns:
            Estimated token count (rough approximation)
        """
        total_chars = sum(len(msg.content) for msg in self.messages)
        # Rough approximation: ~4 characters per token
        return total_chars // 4


class ConversationManager:
    """
    Manages multiple conversations with session support.
    """
    
    def __init__(self):
        """Initialize conversation manager"""
        self.conversations: Dict[str, ChatMemory] = {}
        self.active_conversation: Optional[str] = None
    
    def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional conversation ID
            
        Returns:
            Conversation ID
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        self.conversations[conversation_id] = ChatMemory()
        self.active_conversation = conversation_id
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[ChatMemory]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Chat memory or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def set_active_conversation(self, conversation_id: str):
        """
        Set the active conversation.
        
        Args:
            conversation_id: Conversation ID to set as active
        """
        if conversation_id in self.conversations:
            self.active_conversation = conversation_id
            logger.info(f"Set active conversation: {conversation_id}")
        else:
            logger.warning(f"Conversation not found: {conversation_id}")
    
    def get_active_conversation(self) -> Optional[ChatMemory]:
        """
        Get the active conversation.
        
        Returns:
            Active chat memory or None
        """
        if self.active_conversation:
            return self.conversations.get(self.active_conversation)
        return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            # Clear active if it was the deleted one
            if self.active_conversation == conversation_id:
                self.active_conversation = None
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        
        return False
    
    def list_conversations(self) -> List[str]:
        """
        List all conversation IDs.
        
        Returns:
            List of conversation IDs
        """
        return list(self.conversations.keys())
    
    def get_conversation_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries of all conversations.
        
        Returns:
            Dictionary mapping conversation IDs to summaries
        """
        summaries = {}
        for conv_id, memory in self.conversations.items():
            summaries[conv_id] = memory.get_conversation_summary()
        return summaries