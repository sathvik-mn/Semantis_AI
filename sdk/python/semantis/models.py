"""Response models mirroring OpenAI's API shape."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ChatCompletionMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Usage:
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class CacheMeta:
    hit: str = "miss"
    similarity: float = 0.0
    latency_ms: float = 0.0
    strategy: str = "miss"


@dataclass
class ChatCompletionChoice:
    index: int
    message: ChatCompletionMessage
    finish_reason: str = "stop"


@dataclass
class ChatCompletion:
    id: str
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[ChatCompletionChoice] = field(default_factory=list)
    usage: Optional[Usage] = None
    meta: Optional[CacheMeta] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ChatCompletion":
        choices = []
        for c in data.get("choices", []):
            msg = c.get("message", {})
            choices.append(ChatCompletionChoice(
                index=c.get("index", 0),
                message=ChatCompletionMessage(
                    role=msg.get("role", "assistant"),
                    content=msg.get("content", ""),
                ),
                finish_reason=c.get("finish_reason", "stop"),
            ))

        usage_data = data.get("usage")
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens") if usage_data else None,
            completion_tokens=usage_data.get("completion_tokens") if usage_data else None,
            total_tokens=usage_data.get("total_tokens") if usage_data else None,
        ) if usage_data else None

        meta_data = data.get("meta")
        meta = CacheMeta(
            hit=meta_data.get("hit", "miss"),
            similarity=meta_data.get("similarity", 0.0),
            latency_ms=meta_data.get("latency_ms", 0.0),
            strategy=meta_data.get("strategy", "miss"),
        ) if meta_data else None

        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
            meta=meta,
        )
