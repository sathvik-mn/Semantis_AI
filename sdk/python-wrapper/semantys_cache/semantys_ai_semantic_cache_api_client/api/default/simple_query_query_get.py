from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    prompt: str,
    model: str | Unset = "gpt-4o-mini",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["prompt"] = prompt

    params["model"] = model

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/query",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    prompt: str,
    model: str | Unset = "gpt-4o-mini",
) -> Response[Any | HTTPValidationError]:
    """Simple Query

    Args:
        prompt (str):
        model (str | Unset):  Default: 'gpt-4o-mini'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        prompt=prompt,
        model=model,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    prompt: str,
    model: str | Unset = "gpt-4o-mini",
) -> Any | HTTPValidationError | None:
    """Simple Query

    Args:
        prompt (str):
        model (str | Unset):  Default: 'gpt-4o-mini'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        prompt=prompt,
        model=model,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    prompt: str,
    model: str | Unset = "gpt-4o-mini",
) -> Response[Any | HTTPValidationError]:
    """Simple Query

    Args:
        prompt (str):
        model (str | Unset):  Default: 'gpt-4o-mini'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        prompt=prompt,
        model=model,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    prompt: str,
    model: str | Unset = "gpt-4o-mini",
) -> Any | HTTPValidationError | None:
    """Simple Query

    Args:
        prompt (str):
        model (str | Unset):  Default: 'gpt-4o-mini'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            prompt=prompt,
            model=model,
        )
    ).parsed
