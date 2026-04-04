from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message import ChatMessage


T = TypeVar("T", bound="ChatRequest")


@_attrs_define
class ChatRequest:
    """
    Attributes:
        messages (list[ChatMessage]):
        model (str | Unset):  Default: 'gpt-4o-mini'.
        temperature (float | Unset):  Default: 0.2.
        ttl_seconds (int | Unset):  Default: 604800.
    """

    messages: list[ChatMessage]
    model: str | Unset = "gpt-4o-mini"
    temperature: float | Unset = 0.2
    ttl_seconds: int | Unset = 604800
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        model = self.model

        temperature = self.temperature

        ttl_seconds = self.ttl_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "messages": messages,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if ttl_seconds is not UNSET:
            field_dict["ttl_seconds"] = ttl_seconds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message import ChatMessage

        d = dict(src_dict)
        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ChatMessage.from_dict(messages_item_data)

            messages.append(messages_item)

        model = d.pop("model", UNSET)

        temperature = d.pop("temperature", UNSET)

        ttl_seconds = d.pop("ttl_seconds", UNSET)

        chat_request = cls(
            messages=messages,
            model=model,
            temperature=temperature,
            ttl_seconds=ttl_seconds,
        )

        chat_request.additional_properties = d
        return chat_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
