from src.amm.engine import AMMEngine
from src.amm.liquidity_manager import LiquidityManager
from src.domain.pool import Pool


def test_swap_x_to_y_updates_reserves() -> None:
    """验证 x_to_y 方向交易：池储备正确更新、手续费正确扣除。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    amm = AMMEngine(pool)
    result = amm.swap("x_to_y", 10.0)

    assert result.fee == 0.03
    assert result.amount_out > 0
    assert pool.reserve_x > 1000.0
    assert pool.reserve_y < 1000.0


def test_swap_y_to_x_updates_reserves() -> None:
    """验证 y_to_x 方向交易：池储备正确更新。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    amm = AMMEngine(pool)
    result = amm.swap("y_to_x", 10.0)

    assert result.fee == 0.03
    assert result.amount_out > 0
    assert pool.reserve_x < 1000.0
    assert pool.reserve_y > 1000.0


def test_add_and_remove_liquidity() -> None:
    """验证添加流动性后 LP 份额增加，移除后份额销毁且资产赎回。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    lm = LiquidityManager(pool)

    add_result = lm.add_liquidity(100.0, 100.0)
    assert add_result.consumed_x == 100.0
    assert add_result.consumed_y == 100.0
    assert add_result.minted_shares > 0

    remove_result = lm.remove_liquidity(add_result.minted_shares)
    assert remove_result.amount_x > 0
    assert remove_result.amount_y > 0
    assert remove_result.burned_shares == add_result.minted_shares


def test_add_liquidity_respects_pool_ratio() -> None:
    """验证添加流动性时按池内比例消耗，避免非比例注入改变价格。"""
    pool = Pool(1000.0, 1000.0, 0.003)
    lm = LiquidityManager(pool)

    # 提供不对称的资产（X多Y少），实际消耗应受限于池内比例
    result = lm.add_liquidity(200.0, 50.0)
    # 按比例 50/1000 = 0.05，故消耗 X=1000*0.05=50，Y=1000*0.05=50
    assert result.consumed_x == 50.0
    assert result.consumed_y == 50.0
    assert result.minted_shares > 0
