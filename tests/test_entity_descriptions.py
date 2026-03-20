from typing import Any
from typing import Iterable
from typing import cast
from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorDeviceClass
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
from custom_components.fsolar_modbus.entities.modbus_lambda_sensor import ModbusLambdaSensorDescription
from custom_components.fsolar_modbus.entities.modbus_number import ModbusNumberDescription
from custom_components.fsolar_modbus.entities.modbus_sensor import ModbusSensorDescription
from custom_components.fsolar_modbus.entities.modbus_select import ModbusSelectDescription
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


def test_power_sensors_use_watts() -> None:
    power_entities = [
        entity_factory
        for entity_factory in ENTITIES
        if isinstance(entity_factory, (ModbusSensorDescription, ModbusLambdaSensorDescription))
        and entity_factory.device_class == SensorDeviceClass.POWER
    ]

    assert power_entities

    for entity_factory in power_entities:
        assert entity_factory.native_unit_of_measurement == "W"
        if isinstance(entity_factory, ModbusSensorDescription):
            assert entity_factory.scale == 1.0


def test_voltage_sensors_keep_precision() -> None:
    def _sensor_description_for(
        *, model: InverterModel, connection_type: ConnectionType, key: str
    ) -> ModbusSensorDescription:
        connection_type_profile = INVERTER_PROFILES[model].connection_types[connection_type]
        inv = connection_type_profile.get_inv_for_version(None)

        matches = [
            entity_factory
            for entity_factory in ENTITIES
            if isinstance(entity_factory, ModbusSensorDescription)
            and entity_factory.key == key
            and entity_factory.serialize(inv, connection_type_profile.register_type) is not None
        ]

        assert len(matches) == 1
        return matches[0]

    assert _sensor_description_for(
        model=InverterModel.IVEM,
        connection_type=ConnectionType.AUX,
        key="battery_voltage",
    ).suggested_display_precision == 2
    assert _sensor_description_for(
        model=InverterModel.IVEM,
        connection_type=ConnectionType.AUX,
        key="bms_cv_voltage",
    ).suggested_display_precision == 1
    assert _sensor_description_for(
        model=InverterModel.IVEM,
        connection_type=ConnectionType.AUX,
        key="bms_float_voltage",
    ).suggested_display_precision == 1
    assert _sensor_description_for(
        model=InverterModel.IVEM,
        connection_type=ConnectionType.AUX,
        key="bms_cutoff_voltage",
    ).suggested_display_precision == 1


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
        "addresses": [4621],
        "scale": 0.01,
        "signed": False,
    }
    assert serialized_by_key["battery_current"] == {
        "type": "sensor",
        "key": "battery_current",
        "name": "Battery Current",
        "addresses": [4620],
        "scale": 0.1,
        "signed": True,
    }
    assert serialized_by_key["battery_soc"] == {
        "type": "sensor",
        "key": "battery_soc",
        "name": "Battery SoC",
        "addresses": [4624],
        "scale": 0.1,
        "signed": False,
    }
    assert serialized_by_key["battery_power"] == {
        "type": "sensor",
        "key": "battery_power",
        "name": "Battery Power",
        "addresses": [4362],
        "scale": 1.0,
        "signed": True,
    }
    assert serialized_by_key["battery_power_charge"] == {
        "type": "sensor",
        "key": "battery_power_charge",
        "name": "Battery Power Charge",
        "addresses": [4362],
        "scale": 1.0,
        "signed": True,
    }
    assert serialized_by_key["battery_power_discharge"] == {
        "type": "sensor",
        "key": "battery_power_discharge",
        "name": "Battery Power Discharge",
        "addresses": [4362],
        "scale": 1.0,
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


def test_ivem_configuration_entities_use_documented_registers_and_values() -> None:
    connection_type_profile = INVERTER_PROFILES[InverterModel.IVEM].connection_types[ConnectionType.AUX]
    inv = connection_type_profile.get_inv_for_version(None)

    serialized_by_key = {}
    for entity_factory in ENTITIES:
        serialized = entity_factory.serialize(inv, connection_type_profile.register_type)
        if serialized is not None:
            serialized_by_key[serialized["key"]] = serialized

    assert serialized_by_key["battery_cutoff_voltage"] == {
        "type": "number",
        "key": "battery_cutoff_voltage",
        "name": "Battery Cut-Off Voltage",
        "addresses": [8479],
        "scale": 0.1,
    }
    assert serialized_by_key["charging_source_priority"] == {
        "type": "select",
        "key": "charging_source_priority",
        "name": "Charging Source Priority",
        "addresses": [8492],
        "values": {1: "Solar First", 2: "Solar and Utility First", 3: "Solar Only"},
    }
    assert serialized_by_key["buzzer"] == {
        "type": "select",
        "key": "buzzer",
        "name": "Buzzer",
        "addresses": [8497],
        "values": {0: "Disable", 1: "Enable"},
    }


def test_ivem_configuration_entities_are_selects_or_numbers() -> None:
    connection_type_profile = INVERTER_PROFILES[InverterModel.IVEM].connection_types[ConnectionType.AUX]
    inv = connection_type_profile.get_inv_for_version(None)

    factories = [
        entity_factory
        for entity_factory in ENTITIES
        if entity_factory.serialize(inv, connection_type_profile.register_type) is not None
        and entity_factory.key
        in {
            "ac_output_frequency",
            "application_mode",
            "battery_back_to_charge_voltage",
            "battery_back_to_discharge_voltage",
            "battery_cutoff_voltage",
            "battery_cv_voltage",
            "battery_float_voltage",
            "battery_max_ac_charge_current",
            "battery_max_charge_current",
            "battery_type",
            "buzzer",
            "charging_source_priority",
            "lcd_backlight",
            "output_source_priority",
            "over_temperature_restart",
            "overload_restart",
            "overload_to_bypass",
        }
    ]

    assert factories
    assert any(isinstance(entity_factory, ModbusSelectDescription) for entity_factory in factories)
    assert any(isinstance(entity_factory, ModbusNumberDescription) for entity_factory in factories)


def test_ivem_additional_battery_entities_use_documented_registers_and_scales() -> None:
    connection_type_profile = INVERTER_PROFILES[InverterModel.IVEM].connection_types[ConnectionType.AUX]
    inv = connection_type_profile.get_inv_for_version(None)

    serialized_by_key = {}
    for entity_factory in ENTITIES:
        serialized = entity_factory.serialize(inv, connection_type_profile.register_type)
        if serialized is not None:
            serialized_by_key[serialized["key"]] = serialized

    assert serialized_by_key["battery_line_voltage"] == {
        "type": "sensor",
        "key": "battery_line_voltage",
        "name": "Battery Line Voltage",
        "addresses": [4608],
        "scale": 0.1,
        "signed": False,
    }
    assert serialized_by_key["battery_charge_discharge_limit_voltage"] == {
        "type": "sensor",
        "key": "battery_charge_discharge_limit_voltage",
        "name": "Battery Charge/Discharge Limit Voltage",
        "addresses": [4609],
        "scale": 0.1,
        "signed": False,
    }
    assert serialized_by_key["battery_max_charge_current_limit"] == {
        "type": "sensor",
        "key": "battery_max_charge_current_limit",
        "name": "Battery Max Charge Current Limit",
        "addresses": [4610],
        "scale": 0.1,
        "signed": False,
    }
    assert serialized_by_key["battery_max_discharge_current_limit"] == {
        "type": "sensor",
        "key": "battery_max_discharge_current_limit",
        "name": "Battery Max Discharge Current Limit",
        "addresses": [4611],
        "scale": 0.1,
        "signed": False,
    }
    assert serialized_by_key["battery_system_fault_code"] == {
        "type": "sensor",
        "key": "battery_system_fault_code",
        "name": "Battery System Fault Code",
        "addresses": [4612],
        "scale": None,
        "signed": False,
    }
    assert serialized_by_key["battery_system_status_state"] == {
        "type": "sensor",
        "key": "battery_system_status_state",
        "name": "Battery System Status State",
        "addresses": [4613],
        "scale": None,
        "signed": False,
    }
    assert serialized_by_key["battery_soh"] == {
        "type": "sensor",
        "key": "battery_soh",
        "name": "Battery SoH",
        "addresses": [4625],
        "scale": 0.1,
        "signed": False,
    }
