from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.domain.user import User


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, message: str) -> None:
        self.errors.append(message)

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("; ".join(self.errors))


def validate_pool_params(initial_reserve_x: float, initial_reserve_y: float, fee_rate: float) -> ValidationResult:
    result = ValidationResult()
    if initial_reserve_x < 0:
        result.add("initial_reserve_x must be non-negative")
    if initial_reserve_y < 0:
        result.add("initial_reserve_y must be non-negative")
    if not 0 <= fee_rate < 1:
        result.add("fee_rate must satisfy 0 <= fee_rate < 1")
    return result


def validate_users(users: dict[str, User]) -> ValidationResult:
    result = ValidationResult()
    if not users:
        result.add("at least one user is required")
    for user_id, user in users.items():
        if not str(user_id).strip():
            result.add("user_id must not be empty")
        if user.balance_x < 0 or user.balance_y < 0 or user.lp_shares < 0:
            result.add(f"user {user_id} balances and LP shares must be non-negative")
    return result


def validate_events(events: list[dict[str, Any]], users: dict[str, User] | None = None) -> ValidationResult:
    result = ValidationResult()
    if not events:
        result.add("at least one event is required")

    known_users = set(users or {})
    for index, event in enumerate(events, start=1):
        prefix = f"event #{index}"
        event_type = str(event.get("event_type", "")).strip()
        user_id = str(event.get("user_id", "")).strip()
        if not user_id:
            result.add(f"{prefix}: user_id must not be empty")
        elif known_users and user_id not in known_users:
            result.add(f"{prefix}: user {user_id} is not defined")

        try:
            timestamp = float(event.get("timestamp", index))
            if timestamp < 0:
                result.add(f"{prefix}: timestamp must be non-negative")
        except (TypeError, ValueError):
            result.add(f"{prefix}: timestamp must be numeric")

        if event_type == "swap":
            direction = str(event.get("direction", "")).strip()
            if direction not in {"x_to_y", "y_to_x"}:
                result.add(f"{prefix}: swap direction must be x_to_y or y_to_x")
            _require_positive_number(result, event, "amount_in", prefix)
        elif event_type == "add_liquidity":
            _require_positive_number(result, event, "amount_x", prefix)
            _require_positive_number(result, event, "amount_y", prefix)
        elif event_type == "remove_liquidity":
            _require_positive_number(result, event, "lp_share", prefix)
        else:
            result.add(f"{prefix}: unsupported event_type {event_type!r}")

    return result


def validate_simulation_input(
    *,
    initial_reserve_x: float,
    initial_reserve_y: float,
    fee_rate: float,
    users: dict[str, User],
    events: list[dict[str, Any]],
) -> ValidationResult:
    # 配置文件、Web 表格和 CLI 扩展场景都复用这一层校验，
    # 保证非法输入在进入核心 AMM 计算前就能被解释清楚。
    result = ValidationResult()
    for partial in (
        validate_pool_params(initial_reserve_x, initial_reserve_y, fee_rate),
        validate_users(users),
        validate_events(events, users),
    ):
        result.errors.extend(partial.errors)
    return result


def _require_positive_number(result: ValidationResult, event: dict[str, Any], key: str, prefix: str) -> None:
    try:
        value = float(event.get(key, 0.0))
    except (TypeError, ValueError):
        result.add(f"{prefix}: {key} must be numeric")
        return
    if value <= 0:
        result.add(f"{prefix}: {key} must be positive")
