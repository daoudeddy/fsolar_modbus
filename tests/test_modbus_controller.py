from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from custom_components.fsolar_modbus.client.modbus_client import ModbusClientFailedError
from custom_components.fsolar_modbus.common.register_types import RegisterPollType
from custom_components.fsolar_modbus.common.register_types import InverterModel
from custom_components.fsolar_modbus.const import MAX_READ
from custom_components.fsolar_modbus.modbus_controller import RegisterValue
from custom_components.fsolar_modbus.modbus_controller import ModbusController
from custom_components.fsolar_modbus.vendor.pymodbus import ModbusIOException


@pytest.mark.asyncio
async def test_autodetect_recognizes_ivem_subtype() -> None:
    client = MagicMock()
    client.read_registers = AsyncMock(return_value=[0x50, 0x040F])
    client.close = AsyncMock()

    model, full_model = await ModbusController.autodetect(client, slave=1, adapter_config={MAX_READ: 20})

    assert model == InverterModel.IVEM
    assert full_model == "IVEM8048II"
    client.read_registers.assert_awaited_once()
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_autodetect_recognizes_trex_high_voltage_model() -> None:
    client = MagicMock()
    client.read_registers = AsyncMock(return_value=[0x51, 0x0A08])
    client.close = AsyncMock()

    model, full_model = await ModbusController.autodetect(client, slave=1, adapter_config={MAX_READ: 20})

    assert model == InverterModel.TREX
    assert full_model == "T-REX-5KHP3G01"
    client.read_registers.assert_awaited_once()
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_registers_accepts_verified_silent_write() -> None:
    client = MagicMock()
    client.write_registers = AsyncMock(
        side_effect=ModbusClientFailedError(
            "Error writing registers. Start: 8501; values: [1]; slave: 1",
            client=MagicMock(),
            response=ModbusIOException(
                "Modbus Error: [Input/Output] Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)"
            ),
        )
    )
    client.read_registers = AsyncMock(return_value=[1])

    controller = ModbusController.__new__(ModbusController)
    controller._client = client
    controller._slave = 1
    controller._data = {8501: RegisterValue(poll_type=RegisterPollType.PERIODICALLY, read_value=0)}
    controller._update_listeners = set()

    await controller.write_registers(8501, [1])

    assert controller._data[8501].written_value == 1
    client.read_registers.assert_awaited_once()
