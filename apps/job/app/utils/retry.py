"""Retry decorator with exponential backoff using tenacity."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _log_retry(retry_state: RetryCallState) -> None:
    """Log each retry attempt."""
    logger.warning(
        "retrying",
        attempt=retry_state.attempt_number,
        fn=getattr(retry_state.fn, "__name__", str(retry_state.fn)),
        wait=f"{retry_state.next_action.sleep if retry_state.next_action else 0:.1f}s",  # type: ignore[union-attr]
    )


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator: retry with exponential backoff on specified exceptions."""
    return retry(  # type: ignore[return-value]
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_on),
        before_sleep=_log_retry,
        reraise=True,
    )
