from custom_components.fsolar_modbus.client.custom_modbus_tcp_client import _remaining_poll_timeout_ms


def test_remaining_poll_timeout_ms_converts_seconds_to_milliseconds() -> None:
    assert _remaining_poll_timeout_ms(13.0, 10.0) == 3000
    assert _remaining_poll_timeout_ms(10.001, 10.0) == 1
    assert _remaining_poll_timeout_ms(9.0, 10.0) == 0
