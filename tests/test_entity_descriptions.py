from typing import Any
from typing import Iterable
from typing import cast
from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

from custom_components.fsolar_modbus.common.entity_controller import ModbusControllerEntity
from custom_components.fsolar_modbus.common.register_types import ConnectionType
from custom_components.fsolar_modbus.common.register_types import InverterModel
from custom_components.fsolar_modbus.const import ENTITY_ID_PREFIX
from custom_components.fsolar_modbus.const import INVERTER_BASE
from custom_components.fsolar_modbus.const import INVERTER_CONN
from custom_components.fsolar_modbus.const import UNIQUE_ID_PREFIX
from custom_components.fsolar_modbus.entities.entity_descriptions import ENTITIES
from custom_components.fsolar_modbus.inverter_profiles import INVERTER_PROFILES
from custom_components.fsolar_modbus.inverter_profiles import Version
from custom_components.fsolar_modbus.inverter_profiles import create_entities


@pytest.fixture
def snapshot_json(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.use_extension(extension_class=JSONSnapshotExtension)


async def test_creates_all_entities(hass: HomeAssistant) -> None:
    controller = MagicMock()
    controller.hass = hass

    for profile in INVERTER_PROFILES.values():
        for connection_type, connection_type_profile in profile.connection_types.items():
            for entity_type in [SensorEntity, BinarySensorEntity, SelectEntity, NumberEntity]:
                controller.inverter_details = {
                    INVERTER_BASE: profile.model,
                    INVERTER_CONN: connection_type,
                    ENTITY_ID_PREFIX: "",
                    UNIQUE_ID_PREFIX: "",
                }

                # Asserts if e.g. the ModbusAddressSpecs match
                # We can't test IntegrationSensors (which have depends_on_other_entities=True), as HA throws up saying
                # that the entity it depends on doesn't exist (as we're not actually creating entities).
                entities = create_entities(entity_type, controller, filter_depends_on_other_entites=False)

                for entity in entities:
                    for address in cast(ModbusControllerEntity, entity).addresses:
                        for start, end in connection_type_profile.special_registers.invalid_register_ranges:
                            if start <= address <= end:
                                raise AssertionError(
                                    f"Profile {profile.model} Entity {entity.unique_id} address {address} lies in "
                                    f"range ({start}, {end})"
                                )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "model" in metafunc.fixturenames:
        inputs = []
        for model, profile in INVERTER_PROFILES.items():
            for connection_type, connection_type_profile in profile.connection_types.items():
                for version in connection_type_profile.versions:
                    v = "latest" if version is None else f"v{version}"
                    inputs.append((model, connection_type, v))

        metafunc.parametrize(("model", "connection_type", "version"), inputs)


def test_entities(
    model: InverterModel, connection_type: ConnectionType, version: str, snapshot_json: SnapshotAssertion
) -> None:
    # syrupy doesn't like keys which aren't strings
    def _process(d: Any) -> None:
        if isinstance(d, dict):
            for k, v in d.copy().items():
                if not isinstance(k, str):
                    del d[k]
                    d[str(k)] = v
                _process(v)
        elif isinstance(d, str):
            pass
        elif isinstance(d, Iterable):
            for v in d:
                _process(v)

    connection_type_profile = INVERTER_PROFILES[model].connection_types[connection_type]
    v = None if version == "latest" else Version.parse(version.lstrip("v"))
    inv = connection_type_profile.get_inv_for_version(v)

    entities = []
    for entity_factory in ENTITIES:
        serialized = entity_factory.serialize(inv, connection_type_profile.register_type)
        if serialized is not None:
            _process(serialized)
            entities.append(serialized)

    entities.sort(key=lambda x: x.get("key", ""))

    assert entities == snapshot_json


def test_ivem_entities_use_documented_registers_and_scales() -> None:
    connection_type_profile = INVERTER_PROFILES[InverterModel.IVEM].connection_types[ConnectionType.AUX]
    inv = connection_type_profile.get_inv_for_version(None)

    serialized_by_key = {}
    for entity_factory in ENTITIES:
        serialized = entity_factory.serialize(inv, connection_type_profile.register_type)
        if serialized is not None:
            serialized_by_key[serialized["key"]] = serialized

    assert serialized_by_key["battery_voltage"] == {
        "type": "sensor",
        "key": "battery_voltage",
        "name": "Battery Voltage",
        "addresses": [4360],
        "scale": 0.01,
        "signed": False,
    }
    assert serialized_by_key["battery_current"] == {
        "type": "sensor",
        "key": "battery_current",
        "name": "Battery Current",
        "addresses": [4361],
        "scale": None,
        "signed": True,
    }
    assert serialized_by_key["battery_soc"] == {
        "type": "sensor",
        "key": "battery_soc",
        "name": "Battery SoC",
        "addresses": [4363],
        "scale": None,
        "signed": False,
    }
    assert serialized_by_key["battery_power"] == {
        "type": "sensor",
        "key": "battery_power",
        "name": "Battery Power",
        "addresses": [4362],
        "scale": 0.001,
        "signed": True,
    }
    assert serialized_by_key["battery_power_charge"] == {
        "type": "sensor",
        "key": "battery_power_charge",
        "name": "Battery Power Charge",
        "addresses": [4362],
        "scale": 0.001,
        "signed": True,
    }
    assert serialized_by_key["battery_power_discharge"] == {
        "type": "sensor",
        "key": "battery_power_discharge",
        "name": "Battery Power Discharge",
        "addresses": [4362],
        "scale": 0.001,
        "signed": True,
    }
    assert serialized_by_key["pv1_voltage"] == {
        "type": "sensor",
        "key": "pv1_voltage",
        "name": "PV1 Voltage",
        "addresses": [4390],
        "scale": 0.1,
        "signed": True,
    }
    assert serialized_by_key["pv_energy_total"] == {
        "type": "sensor",
        "key": "pv_energy_total",
        "name": "PV Energy Total",
        "addresses": [4412, 4411, 4410, 4409],
        "scale": 0.001,
        "signed": False,
    }
    assert serialized_by_key["load_energy_total"] == {
        "type": "sensor",
        "key": "load_energy_total",
        "name": "Load Energy Total",
        "addresses": [4428, 4427, 4426, 4425],
        "scale": 0.001,
        "signed": False,
    }
    assert serialized_by_key["smart_port_status"] == {
        "type": "inverter-state-sensor",
        "key": "smart_port_status",
        "name": "Smart Port Status",
        "addresses": [4461],
        "states": ["Generator Input", "Smart Load Output"],
    }
