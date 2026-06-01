"""边界条件和极端场景测试。

覆盖极端池状态、大额交易、LP 边界操作、数值精度、事件顺序和输入校验，
补充基础测试未覆盖的边界路径。
"""

from math import isclose

import pytest

from src.amm.engine import AMMEngine
from src.amm.liquidity_manager import LiquidityManager
from src.analytics.impermanent_loss import (
    impermanent_loss_from_price_ratio,
    impermanent_loss_pct,
)
from src.analytics.pnl import summarize_user_pnl
from src.analytics.slippage import calculate_slippage_pct
from src.application.validation import (
    ValidationResult,
    validate_events,
    validate_pool_params,
    validate_users,
)
from src.domain.exceptions import InsufficientBalanceError, InsufficientLiquidityError
from src.domain.pool import Pool
from src.domain.user import User
from src.simulator.engine import SimulatorEngine
from src.simulator.event import Event, EventType


# ── 极端池状态 ──────────────────────────────────────────────────────


def test_swap_fails_when_reserves_are_zero() -> None:
    """储备为 0 时交易应抛出 InsufficientBalanceError。"""
    pool = Pool(0.0, 0.0, 0.003)
    amm = AMMEngine(pool)
    with pytest.raises(InsufficientBalanceError):
        amm.swap("x_to_y", 10.0)


def test_swap_fails_for_zero_or_negative_amount() -> None:
    """输入金额 ≤ 0 时交易应抛出异常。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    amm = AMMEngine(pool)
    with pytest.raises(InsufficientBalanceError):
        amm.swap("x_to_y", 0.0)
    with pytest.raises(InsufficientBalanceError):
        amm.swap("x_to_y", -1.0)


def test_swap_small_amount_with_tiny_reserves() -> None:
    """储备极小时小额交易应正常完成且保持合理精度。"""
    pool = Pool(0.001, 0.001, 0.003)
    amm = AMMEngine(pool)
    result = amm.swap("x_to_y", 0.0001)
    assert result.amount_out > 0
    assert result.fee > 0
    # 交易后恒定乘积不能减小
    assert pool.invariant >= 0.001 * 0.001 - 1e-15


# ── 大额交易冲击 ────────────────────────────────────────────────────


def test_large_trade_near_pool_exhaustion() -> None:
    """输入金额接近池储备 99% 时仍应有合理输出且不耗尽池子。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    amm = AMMEngine(pool)
    # 输入 990 X，扣除手续费后 effective_in = 990 * 0.997 = 987.03
    result = amm.swap("x_to_y", 990.0)
    assert result.amount_out > 0
    # 池子不会完全耗尽
    assert pool.reserve_x > 0
    assert pool.reserve_y > 0
    # 滑点应该非常显著
    assert result.slippage_pct is not None
    assert result.slippage_pct > 40  # 大额交易应有显著滑点（约 49.8%）


def test_very_large_trade_slippage_scales_with_size() -> None:
    """交易量越大滑点越高。"""
    pool1 = Pool(1000.0, 1000.0, 0.0)
    pool2 = Pool(1000.0, 1000.0, 0.0)
    result_small = AMMEngine(pool1).swap("x_to_y", 10.0)
    result_large = AMMEngine(pool2).swap("x_to_y", 100.0)
    assert result_small.slippage_pct is not None
    assert result_large.slippage_pct is not None
    assert result_large.slippage_pct > result_small.slippage_pct


# ── LP 边界操作 ─────────────────────────────────────────────────────


def test_remove_all_lp_shares() -> None:
    """移除全部已添加的 LP 份额后池总份额回到添加前水平。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    lm = LiquidityManager(pool)
    shares_before = pool.total_lp_shares  # 初始 sqrt(1000*1000) = 1000
    add = lm.add_liquidity(100.0, 100.0)

    # 移除刚添加的全部份额，总份额应回到原始值
    remove = lm.remove_liquidity(add.minted_shares)
    assert remove.burned_shares == add.minted_shares
    assert pool.total_lp_shares == shares_before
    assert pool.reserve_x == 1000.0
    assert pool.reserve_y == 1000.0


def test_remove_more_lp_than_owned_fails() -> None:
    """移除超过持有的 LP 份额应抛出异常。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    lm = LiquidityManager(pool)
    with pytest.raises(InsufficientLiquidityError):
        lm.remove_liquidity(999999.0)


def test_add_liquidity_to_empty_pool() -> None:
    """向空池（储备为 0）首次添加流动性，应按 sqrt(x*y) 铸造份额。"""
    pool = Pool(0.0, 0.0, 0.003)
    lm = LiquidityManager(pool)
    result = lm.add_liquidity(500.0, 500.0)
    assert result.minted_shares > 0
    assert pool.reserve_x == 500.0
    assert pool.reserve_y == 500.0
    # sqrt(500*500) = 500
    assert result.minted_shares == 500.0


# ── 极端价格比 ──────────────────────────────────────────────────────


def test_impermanent_loss_extreme_ratio() -> None:
    """价格比极值（1000x）时无常损失符合理论公式。"""
    # r = 1000 → IL = 2*sqrt(1000)/(1+1000) - 1 ≈ -0.938
    il = impermanent_loss_from_price_ratio(1000.0)
    expected = 2 * (1000 ** 0.5) / 1001 - 1
    assert isclose(il, expected, rel_tol=1e-10)

    # r → ∞ 时 IL → -1 (100% 损失)
    il_huge = impermanent_loss_from_price_ratio(1e12)
    assert il_huge < -0.998  # 接近 -1


def test_impermanent_loss_price_unchanged_is_zero() -> None:
    """价格不变时无常损失为 0。"""
    assert impermanent_loss_pct(2.0, 2.0) == 0.0
    assert impermanent_loss_pct(0.5, 0.5) == 0.0


# ── 手续费率边界 ────────────────────────────────────────────────────


def test_zero_fee_rate_swap() -> None:
    """手续费率为 0 时 fee=0，effective_in = amount_in。"""
    pool = Pool(1000.0, 1000.0, 0.0)
    amm = AMMEngine(pool)
    result = amm.swap("x_to_y", 10.0)
    assert result.fee == 0.0
    assert result.effective_amount_in == 10.0
    # 0 费率时 k 应严格不变（无手续费沉淀）
    assert isclose(pool.invariant, 1000.0 * 1000.0, rel_tol=1e-12)


def test_high_fee_rate_near_one() -> None:
    """高手续费率（0.99）时 effective_in 极小，输出很少。"""
    pool = Pool(1000.0, 1000.0, 0.99)
    amm = AMMEngine(pool)
    result = amm.swap("x_to_y", 10.0)
    assert result.fee == 9.9
    assert isclose(result.effective_amount_in, 0.1, rel_tol=1e-12)
    assert result.amount_out > 0
    # 手续费极高，k 显著增长
    assert pool.invariant > 1000.0 * 1000.0


# ── 收益率计算 ──────────────────────────────────────────────────────


def test_user_pnl_with_no_lp_or_trades_is_zero() -> None:
    """用户无交易无 LP 时 PnL 应为 0。"""
    initial = {"alice": User("alice", balance_x=10.0, balance_y=10.0)}
    current = {"alice": User("alice", balance_x=10.0, balance_y=10.0)}
    pool = Pool(100.0, 100.0, 0.003)
    summary = summarize_user_pnl(initial, current, pool, price_y_per_x=1.0)
    assert summary["alice"].total_pnl_in_y == 0.0
    assert summary["alice"].wallet_pnl_in_y == 0.0


def test_user_pnl_detects_new_user() -> None:
    """动态创建的新用户应被 PnL 统计正确覆盖。"""
    initial = {"alice": User("alice", balance_x=10.0, balance_y=10.0)}
    current = {
        "alice": User("alice", balance_x=5.0, balance_y=15.0),
        "bob": User("bob", balance_x=0.0, balance_y=0.0),
    }
    pool = Pool(100.0, 100.0, 0.003)
    summary = summarize_user_pnl(initial, current, pool, price_y_per_x=1.0)
    assert "bob" in summary
    assert summary["bob"].total_pnl_in_y == 0.0


# ── 事件顺序 ────────────────────────────────────────────────────────


def test_same_timestamp_events_preserve_enqueue_order() -> None:
    """同一 timestamp 的多个事件保持入队顺序执行。"""
    pool = Pool(1000.0, 1000.0, 0.0)
    users = {"alice": User("alice", balance_x=100.0, balance_y=0.0)}
    engine = SimulatorEngine(pool, users)

    # 两个同时间 swap，后面的依赖前面的价格变动
    events = [
        Event(
            timestamp=1.0,
            event_id=1,
            event_type=EventType.SWAP,
            user_id="alice",
            payload={"direction": "x_to_y", "amount_in": 5.0},
        ),
        Event(
            timestamp=1.0,
            event_id=2,
            event_type=EventType.SWAP,
            user_id="alice",
            payload={"direction": "x_to_y", "amount_in": 5.0},
        ),
    ]
    result = engine.run(events)
    assert len(result.records) == 2
    # 第二笔交易的 price_before 应该等于第一笔交易后的价格
    assert result.records[0].event_id == 1
    assert result.records[1].event_id == 2


# ── 滑点边界 ────────────────────────────────────────────────────────


def test_slippage_none_when_price_invalid() -> None:
    """无效价格时滑点返回 None。"""
    assert calculate_slippage_pct(0.0, 1.0) is None
    assert calculate_slippage_pct(float("inf"), 1.0) is None
    assert calculate_slippage_pct(1.0, None) is None


# ── 输入校验边界 ────────────────────────────────────────────────────


def test_validate_pool_rejects_invalid_fee() -> None:
    """费率 ≥ 1 或 < 0 应被校验拒绝。"""
    r = validate_pool_params(100.0, 100.0, 1.0)
    assert not r.ok
    r2 = validate_pool_params(100.0, 100.0, -0.1)
    assert not r2.ok
    r3 = validate_pool_params(100.0, 100.0, 0.003)
    assert r3.ok


def test_validate_users_rejects_negative_balances() -> None:
    """用户余额为负应被校验拒绝。"""
    r = validate_users({"alice": User("alice", balance_x=-1.0, balance_y=0.0)})
    assert not r.ok
    r2 = validate_users({})
    assert not r2.ok  # 至少需要一个用户


def test_validate_events_rejects_unknown_user() -> None:
    """事件引用未声明的用户应被校验拒绝。"""
    r = validate_events(
        [{"timestamp": 1, "event_type": "swap", "user_id": "ghost", "direction": "x_to_y", "amount_in": 1.0}],
        users={"alice"},
    )
    assert not r.ok
    assert any("ghost" in error for error in r.errors)
