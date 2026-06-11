from src.application.validation import validate_events, validate_simulation_input, validate_users
from src.domain.user import User


def test_validate_simulation_input_rejects_invalid_values() -> None:
    result = validate_simulation_input(
        initial_reserve_x=-1.0,
        initial_reserve_y=1000.0,
        fee_rate=1.0,
        users={"alice": User("alice", balance_x=-1.0)},
        events=[{"timestamp": 1, "event_type": "swap", "user_id": "bob", "direction": "bad", "amount_in": 0}],
    )

    assert not result.ok
    assert any("initial_reserve_x" in error for error in result.errors)
    assert any("fee_rate" in error for error in result.errors)
    assert any("direction" in error for error in result.errors)


def test_validate_simulation_input_accepts_default_shape() -> None:
    result = validate_simulation_input(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        users={"alice": User("alice", balance_x=10.0, balance_y=10.0)},
        events=[{"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 1}],
    )

    assert result.ok


def test_validate_simulation_input_rejects_single_sided_initial_pool() -> None:
    result = validate_simulation_input(
        initial_reserve_x=1000.0,
        initial_reserve_y=0.0,
        fee_rate=0.003,
        users={"alice": User("alice", balance_x=10.0, balance_y=10.0)},
        events=[{"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 1}],
    )

    assert not result.ok
    assert any("both positive or both zero" in error for error in result.errors)


def test_validate_simulation_input_rejects_excess_initial_lp_shares() -> None:
    result = validate_simulation_input(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        users={"alice": User("alice", balance_x=10.0, balance_y=10.0, lp_shares=1000.1)},
        events=[{"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 1}],
    )

    assert not result.ok
    assert any("LP shares" in error for error in result.errors)


def test_validate_users_rejects_non_finite_balances() -> None:
    result = validate_users({
        "alice": User("alice", balance_x=float("nan"), balance_y=float("inf"), lp_shares=float("-inf")),
    })

    assert not result.ok
    assert any("balance_x must be finite" in error for error in result.errors)
    assert any("balance_y must be finite" in error for error in result.errors)
    assert any("lp_shares must be finite" in error for error in result.errors)


def test_validate_events_rejects_non_finite_numbers() -> None:
    result = validate_events(
        [
            {
                "timestamp": float("inf"),
                "event_type": "swap",
                "user_id": "alice",
                "direction": "x_to_y",
                "amount_in": float("nan"),
            }
        ],
        {"alice": User("alice", balance_x=10.0, balance_y=10.0)},
    )

    assert not result.ok
    assert any("timestamp must be finite" in error for error in result.errors)
    assert any("amount_in must be finite" in error for error in result.errors)
