from src.application.validation import validate_simulation_input
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
