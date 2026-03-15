from typing import Any
from typing import Awaitable
from typing import Callable
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from custom_components.fsolar_modbus.common.exceptions import AutoconnectFailedError
from custom_components.fsolar_modbus.const import SERIAL
from custom_components.fsolar_modbus.const import TCP
from custom_components.fsolar_modbus.flow.adapter_flow_segment import AdapterFlowSegment
from custom_components.fsolar_modbus.flow.inverter_data import InverterData
from custom_components.fsolar_modbus.inverter_adapters import ADAPTERS


class _FakeFlow:
    def __init__(self) -> None:
        self.hass = MagicMock()

    async def with_default_form(
        self,
        body: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        user_input: dict[str, Any] | None,
        _step_id: str,
        _data_schema: Any,
        *,
        suggested_values: dict[str, Any] | None = None,
        description_placeholders: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        del suggested_values, description_placeholders
        assert user_input is not None
        return await body(user_input)


@pytest.mark.asyncio
async def test_tcp_adapter_step_passes_network_args_to_autodetect() -> None:
    adapter = ADAPTERS["network_other"]
    inverter_data = InverterData(adapter_type=adapter.adapter_type, adapter=adapter)

    async def on_complete() -> dict[str, Any]:
        return {"type": "create_entry"}

    segment = AdapterFlowSegment(_FakeFlow(), inverter_data, [], on_complete)
    autodetect = AsyncMock()

    segment._autodetect_modbus_and_save_to_inverter_data = autodetect

    result = await segment.async_step_tcp_adapter(
        {
            "protocol": TCP,
            "adapter_host": "192.0.2.10",
            "adapter_port": 1502,
            "modbus_slave": 3,
        }
    )

    assert result == {"type": "create_entry"}
    autodetect.assert_awaited_once_with(
        protocol=TCP,
        host="192.0.2.10:1502",
        slave=3,
        adapter=adapter,
    )


@pytest.mark.asyncio
async def test_network_autodetect_clears_serial_baudrate(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ADAPTERS["network_other"]
    inverter_data = InverterData(adapter_type=adapter.adapter_type, adapter=adapter, modbus_serial_baud=2400)

    async def on_complete() -> dict[str, Any]:
        return {"type": "create_entry"}

    segment = AdapterFlowSegment(_FakeFlow(), inverter_data, [], on_complete)
    modbus_client = MagicMock()
    modbus_client_ctor = MagicMock(return_value=modbus_client)
    autodetect = AsyncMock(return_value=("h3_pro", "H3_PRO-AUX"))

    monkeypatch.setattr(
        "custom_components.fsolar_modbus.flow.adapter_flow_segment.ModbusClient",
        modbus_client_ctor,
    )
    monkeypatch.setattr(
        "custom_components.fsolar_modbus.flow.adapter_flow_segment.ModbusController.autodetect",
        autodetect,
    )

    await segment._autodetect_modbus_and_save_to_inverter_data(
        protocol=TCP,
        host="192.0.2.10:1502",
        slave=3,
        adapter=adapter,
    )

    assert inverter_data.inverter_base_model == "h3_pro"
    assert inverter_data.inverter_model == "H3_PRO-AUX"
    assert inverter_data.inverter_protocol == TCP
    assert inverter_data.modbus_slave == 3
    assert inverter_data.modbus_serial_baud is None
    assert inverter_data.host == "192.0.2.10:1502"
    modbus_client_ctor.assert_called_once_with(
        segment._flow.hass,
        TCP,
        adapter,
        {"host": "192.0.2.10", "port": 1502},
    )
    autodetect.assert_awaited_once_with(
        modbus_client,
        3,
        adapter.config.inverter_config(TCP),
    )


@pytest.mark.asyncio
async def test_serial_autodetect_retries_known_baudrates(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ADAPTERS["serial_other"]
    inverter_data = InverterData(adapter_type=adapter.adapter_type, adapter=adapter)

    async def on_complete() -> dict[str, Any]:
        return {"type": "create_entry"}

    segment = AdapterFlowSegment(_FakeFlow(), inverter_data, [], on_complete)
    modbus_client_ctor = MagicMock(side_effect=[MagicMock(), MagicMock()])
    autodetect = AsyncMock(
        side_effect=[
            AutoconnectFailedError([]),
            ("IVEM", "IVEM8048II"),
        ]
    )

    monkeypatch.setattr(
        "custom_components.fsolar_modbus.flow.adapter_flow_segment.ModbusClient",
        modbus_client_ctor,
    )
    monkeypatch.setattr(
        "custom_components.fsolar_modbus.flow.adapter_flow_segment.ModbusController.autodetect",
        autodetect,
    )

    await segment._autodetect_modbus_and_save_to_inverter_data(
        protocol=SERIAL,
        host="/dev/ttyUSB0",
        slave=1,
        adapter=adapter,
        baudrate=2400,
    )

    assert inverter_data.inverter_base_model == "IVEM"
    assert inverter_data.inverter_model == "IVEM8048II"
    assert inverter_data.inverter_protocol == SERIAL
    assert inverter_data.modbus_slave == 1
    assert inverter_data.modbus_serial_baud == 9600
    assert inverter_data.host == "/dev/ttyUSB0"
    assert modbus_client_ctor.call_args_list == [
        ((segment._flow.hass, SERIAL, adapter, {"port": "/dev/ttyUSB0", "baudrate": 2400}),),
        ((segment._flow.hass, SERIAL, adapter, {"port": "/dev/ttyUSB0", "baudrate": 9600}),),
    ]
