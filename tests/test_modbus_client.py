from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from custom_components.fsolar_modbus.client.modbus_client import ModbusClient
from custom_components.fsolar_modbus.vendor.pymodbus import WriteSingleRegisterResponse


@pytest.mark.asyncio
async def test_write_registers_disables_retry_on_empty_for_write_calls() -> None:
    client = ModbusClient.__new__(ModbusClient)
    client._client = MagicMock()
    client._client.transaction = MagicMock(retry_on_empty=True)

    async def _fake_async_pymodbus_call(*_args, **_kwargs):
        assert client._client.transaction.retry_on_empty is False
        return WriteSingleRegisterResponse(address=8501, value=1)

    client._async_pymodbus_call = AsyncMock(side_effect=_fake_async_pymodbus_call)

    await client.write_registers(8501, [1], 1)

    assert client._client.transaction.retry_on_empty is True
