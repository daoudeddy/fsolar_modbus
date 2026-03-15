from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from custom_components.fsolar_modbus.common.register_types import InverterModel
from custom_components.fsolar_modbus.const import MAX_READ
from custom_components.fsolar_modbus.modbus_controller import ModbusController


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
