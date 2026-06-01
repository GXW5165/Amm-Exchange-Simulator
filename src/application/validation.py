from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import Any

from src.domain.user import User


@dataclass
class ValidationResult:
    """输入校验结果。

    errors 为空表示校验通过；调用方可以用 ok 判断，也可以直接调用
    raise_for_errors 把错误聚合成 ValueError。
    """

    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """是否没有校验错误。"""
        return not self.errors

    def add(self, message: str) -> None:
        """追加一条校验错误。"""
        self.errors.append(message)

    def raise_for_errors(self) -> None:
        """如果存在错误，抛出包含全部错误信息的 ValueError。"""
        if self.errors:
            raise ValueError("; ".join(self.errors))


def validate_pool_params(initial_reserve_x: float, initial_reserve_y: float, fee_rate: float) -> ValidationResult:
    """校验资金池初始储备和手续费率。"""
    result = ValidationResult()
    if not isfinite(initial_reserve_x):
        result.add("initial_reserve_x must be finite")
    if not isfinite(initial_reserve_y):
        result.add("initial_reserve_y must be finite")
    if not isfinite(fee_rate):
        result.add("fee_rate must be finite")
    if initial_reserve_x < 0:
        result.add("initial_reserve_x must be non-negative")
    if initial_reserve_y < 0:
        result.add("initial_reserve_y must be non-negative")
    if not 0 <= fee_rate < 1:
        result.add("fee_rate must satisfy 0 <= fee_rate < 1")
    if (initial_reserve_x == 0) ^ (initial_reserve_y == 0):
        result.add("initial reserves must be both positive or both zero")
    return result


def validate_users(users: dict[str, User]) -> ValidationResult:
    """校验用户集合和用户初始资产。"""
    result = ValidationResult()
    if not users:
        result.add("at least one user is required")
    for user_id, user in users.items():
        if not str(user_id).strip():
            result.add("user_id must not be empty")
        if user.balance_x < 0 or user.balance_y < 0 or user.lp_shares < 0:
            result.add(f"user {user_id} balances and LP shares must be non-negative")
    return result


def validate_initial_lp_ownership(
    *,
    initial_reserve_x: float,
    initial_reserve_y: float,
    users: dict[str, User],
    initial_lp_owner: str | None = "protocol",
) -> ValidationResult:
    """校验初始 LP 份额归属是否能与初始池规模匹配。

    初始池非空时 Pool 会按 sqrt(x*y) 生成总 LP 份额；用户配置可显式持有
    其中一部分，剩余份额会在运行前归给 initial_lp_owner，避免出现无主 LP。
    """
    result = ValidationResult()
    total_user_lp = sum(user.lp_shares for user in users.values())
    if initial_reserve_x > 0 and initial_reserve_y > 0:
        initial_total_lp = sqrt(initial_reserve_x * initial_reserve_y)
        if total_user_lp > initial_total_lp + 1e-9:
            result.add("sum of user LP shares exceeds initial pool total LP shares")
        if total_user_lp < initial_total_lp - 1e-9 and not str(initial_lp_owner or "").strip():
            result.add("initial_lp_owner is required when initial LP shares are not fully assigned")
    elif total_user_lp > 1e-9:
        result.add("users cannot hold LP shares when initial pool has no liquidity")
    return result


def validate_events(events: list[dict[str, Any]], users: dict[str, User] | None = None) -> ValidationResult:
    """校验事件序列。

    如果传入 users，会额外检查事件中的 user_id 是否已经在用户配置中声明。
    """
    result = ValidationResult()

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
    initial_lp_owner: str | None = "protocol",
) -> ValidationResult:
    # 配置文件、Web 表格和 CLI 扩展场景都复用这一层校验，
    # 保证非法输入在进入核心 AMM 计算前就能被解释清楚。
    result = ValidationResult()
    for partial in (
        validate_pool_params(initial_reserve_x, initial_reserve_y, fee_rate),
        validate_users(users),
        validate_initial_lp_ownership(
            initial_reserve_x=initial_reserve_x,
            initial_reserve_y=initial_reserve_y,
            users=users,
            initial_lp_owner=initial_lp_owner,
        ),
        validate_events(events, users),
    ):
        result.errors.extend(partial.errors)
    return result


def _require_positive_number(result: ValidationResult, event: dict[str, Any], key: str, prefix: str) -> None:
    """校验某个事件字段存在且为正数。"""
    try:
        value = float(event.get(key, 0.0))
    except (TypeError, ValueError):
        result.add(f"{prefix}: {key} must be numeric")
        return
    if value <= 0:
        result.add(f"{prefix}: {key} must be positive")
