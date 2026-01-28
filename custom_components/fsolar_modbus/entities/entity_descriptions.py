"""Holds all entity descriptions for all entities across all inverters."""

import itertools
from typing import Iterable

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorStateClass

from ..common.register_types import Inv
from ..common.register_types import RegisterType
from .charge_period_descriptions import CHARGE_PERIODS
from .entity_factory import EntityFactory
from .inverter_model_spec import EntitySpec
from .inverter_model_spec import ModbusAddressesSpec
from .inverter_model_spec import ModbusAddressSpec
from .modbus_battery_sensor import ModbusBatterySensorDescription
from .modbus_fault_sensor import STANDARD_FAULTS
from .modbus_fault_sensor import TREX_FAULTS
from .modbus_fault_sensor import FaultSet
from .modbus_fault_sensor import ModbusFaultSensorDescription
from .modbus_inverter_state_sensor import TREX_INVERTER_STATES
from .modbus_inverter_state_sensor import ModbusG2InverterStateSensorDescription
from .modbus_inverter_state_sensor import ModbusInverterStateSensorDescription
from .modbus_lambda_sensor import ModbusLambdaSensorDescription
from .modbus_number import ModbusNumberDescription
from .modbus_sensor import ModbusSensorDescription
from .modbus_version_sensor import ModbusVersionSensorDescription
from .modbus_work_mode_select import ModbusWorkModeSelectDescription
from .remote_control_description import REMOTE_CONTROL_DESCRIPTION
from .validation import Min
from .validation import Range

# hass type hints are messed up, and mypy doesn't see inherited dataclass properties on the EntityDescriptions
# mypy: disable-error-code="call-arg"


BMS_CONNECT_STATE_ADDRESS = [
    ModbusAddressSpec(holding=4607, models=Inv.TREX),
]


def _version_entities() -> Iterable[EntityFactory]:
    # Named so that they sort together
    def _master_version(address: list[ModbusAddressSpec], is_hex: bool) -> ModbusVersionSensorDescription:
        return ModbusVersionSensorDescription(
            key="master_version",
            address=address,
            is_hex=is_hex,
            name="Version: Master",
            icon="mdi:source-branch",
        )

    yield _master_version(
        address=[
            ModbusAddressSpec(holding=35016, models=Inv.GWETP),
            ModbusAddressSpec(holding=63549, models=Inv.TREX),
        ],
        is_hex=False,
    )

    def _slave_version(address: list[ModbusAddressSpec], is_hex: bool) -> ModbusVersionSensorDescription:
        return ModbusVersionSensorDescription(
            key="slave_version",
            address=address,
            is_hex=is_hex,
            name="Version: Slave",
            icon="mdi:source-branch",
        )

    yield _slave_version(
        address=[
            ModbusAddressSpec(holding=35017, models=Inv.GWETP),
            ModbusAddressSpec(holding=63550, models=Inv.TREX),
        ],
        is_hex=False,
    )

    def _manager_version(address: list[ModbusAddressSpec], is_hex: bool) -> ModbusVersionSensorDescription:
        return ModbusVersionSensorDescription(
            key="manager_version",
            address=address,
            is_hex=is_hex,
            name="Version: Manager",
            icon="mdi:source-branch",
        )

    yield _manager_version(
        address=[
            ModbusAddressSpec(holding=35019, models=Inv.GWETP),
            ModbusAddressSpec(holding=63553, models=Inv.TREX),
        ],
        is_hex=False,
    )


def _pv_entities() -> Iterable[EntityFactory]:
    def _pv_voltage(key: str, addresses: list[ModbusAddressesSpec], name: str) -> EntityFactory:
        return ModbusSensorDescription(
            key=key,
            addresses=addresses,
            name=name,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="V",
            scale=0.1,
            round_to=1,
            # This can go negative if no panels are attached
        )

    def _pv_current(key: str, addresses: list[ModbusAddressesSpec], name: str, scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key=key,
            addresses=addresses,
            name=name,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="A",
            scale=scale,
            round_to=1,
            # This can a small amount negative
            post_process=lambda x: max(x, 0),
            validate=[Range(0, 100)],
        )

    def _pv_power(key: str, addresses: list[ModbusAddressesSpec], name: str) -> EntityFactory:
        return ModbusSensorDescription(
            key=key,
            addresses=addresses,
            name=name,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:solar-power-variant-outline",
            scale=0.001,
            round_to=0.01,
            # This can go negative if no panels are attached
            post_process=lambda x: max(x, 0),
        )

    yield _pv_voltage(
        key="pv1_voltage",
        addresses=[
            ModbusAddressesSpec(holding=[35103], models=Inv.GWETP),
            ModbusAddressesSpec(holding=[4375], models=Inv.TREX),
        ],
        name="PV1 Voltage",
    )
    yield _pv_current(
        key="pv1_current",
        addresses=[
            ModbusAddressesSpec(holding=[4376], models=Inv.TREX),
        ],
        name="PV1 Current",
        scale=0.1,
    )
    yield _pv_power(
        key="pv1_power",
        addresses=[
            ModbusAddressesSpec(holding=[35105], models=Inv.GWETP),
            ModbusAddressesSpec(holding=[4377], models=Inv.TREX),
        ],
        name="PV1 Power",
    )
    yield _pv_voltage(
        key="pv2_voltage",
        addresses=[
            ModbusAddressesSpec(holding=[4378], models=Inv.TREX),
        ],
        name="PV2 Voltage",
    )
    yield _pv_current(
        key="pv2_current",
        addresses=[
            ModbusAddressesSpec(holding=[4379], models=Inv.TREX),
        ],
        name="PV2 Current",
        scale=0.1,
    )
    yield _pv_power(
        key="pv2_power",
        addresses=[
            ModbusAddressesSpec(holding=[4380], models=Inv.TREX),
        ],
        name="PV2 Power",
    )

    yield ModbusLambdaSensorDescription(
        key="pv_power",
        models=[
            EntitySpec(
                register_types=[RegisterType.INPUT, RegisterType.HOLDING],
                models=Inv.ALL & ~(Inv.KH_SET | Inv.H3_PRO_SET | Inv.H3_SMART),
            ),
        ],
        sources=["pv1_power", "pv2_power"],
        method=sum,
        name="PV Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kW",
        icon="mdi:solar-power-variant-outline",
    )


def _h3_current_voltage_power_entities() -> Iterable[EntityFactory]:
    def _grid_voltage(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"grid_voltage_{phase}",
            addresses=addresses,
            name=f"Grid Voltage {phase}",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="V",
            scale=0.1,
            round_to=1,
            signed=False,
            validate=[Range(0, 300)],
        )

    yield _grid_voltage(
        "R",
        addresses=[
            ModbusAddressesSpec(holding=[4361], models=Inv.TREX),
        ],
    )
    yield _grid_voltage(
        "S",
        addresses=[
            ModbusAddressesSpec(holding=[4384], models=Inv.TREX),
        ],
    )
    yield _grid_voltage(
        "T",
        addresses=[
            ModbusAddressesSpec(holding=[4388], models=Inv.TREX),
        ],
    )

    def _inverter_current(phase: str, addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"inverter_current_{phase}",
            addresses=addresses,
            name=f"Inverter Current {phase}",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="A",
            scale=scale,
            round_to=1,
            validate=[Range(0, 100)],
        )

    def _inverter_current_set(
        r_addresses: list[ModbusAddressesSpec],
        s_addresses: list[ModbusAddressesSpec],
        t_addresses: list[ModbusAddressesSpec],
        scale: float,
    ) -> Iterable[EntityFactory]:
        yield _inverter_current("R", addresses=r_addresses, scale=scale)
        yield _inverter_current("S", addresses=s_addresses, scale=scale)
        yield _inverter_current("T", addresses=t_addresses, scale=scale)

    yield from _inverter_current_set(
        r_addresses=[ModbusAddressesSpec(holding=[4362], models=Inv.TREX)],
        s_addresses=[ModbusAddressesSpec(holding=[4385], models=Inv.TREX)],
        t_addresses=[ModbusAddressesSpec(holding=[4389], models=Inv.TREX)],
        scale=0.1,
    )

    def _inverter_power(phase: str | None, addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""
        return ModbusSensorDescription(
            key=f"inverter_power{key_suffix}",
            addresses=addresses,
            name=f"Inverter Power{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )

    yield _inverter_power(
        "R",
        addresses=[
            ModbusAddressesSpec(holding=[4364], models=Inv.TREX),
        ],
        scale=0.001,
    )
    yield _inverter_power(
        "S",
        addresses=[
            ModbusAddressesSpec(holding=[4387], models=Inv.TREX),
        ],
        scale=0.001,
    )
    yield _inverter_power(
        "T",
        addresses=[
            ModbusAddressesSpec(holding=[4391], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _backup_volt(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"backup_volt_{phase}",
            addresses=addresses,
            entity_registry_enabled_default=False,
            name=f"Backup Voltage_{phase}",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="V",
            scale=0.1,
            round_to=1,
            signed=False,
            validate=[Range(0, 300)],
        )

    yield _backup_volt("R", addresses=[ModbusAddressesSpec(holding=[39201], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _backup_volt("S", addresses=[ModbusAddressesSpec(holding=[39202], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _backup_volt("T", addresses=[ModbusAddressesSpec(holding=[39203], models=Inv.H3_PRO_SET | Inv.H3_SMART)])

    def _backup_current(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"backup_current_{phase}",
            addresses=addresses,
            entity_registry_enabled_default=False,
            name=f"Backup Current {phase}",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="A",
            scale=0.001,
            round_to=1,
            validate=[Range(0, 100)],
        )

    yield _backup_current(
        "R", addresses=[ModbusAddressesSpec(holding=[39205, 39204], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
    )
    yield _backup_current(
        "S", addresses=[ModbusAddressesSpec(holding=[39207, 39206], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
    )
    yield _backup_current(
        "T", addresses=[ModbusAddressesSpec(holding=[39209, 39208], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
    )

    def _backup_power(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"backup_power_{phase}",
            addresses=addresses,
            name=f"Backup Power {phase}",
            entity_registry_enabled_default=False,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:power-socket",
            scale=0.001,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )

    yield _backup_power("R", addresses=[ModbusAddressesSpec(holding=[4531], models=Inv.TREX)])
    yield _backup_power("S", addresses=[ModbusAddressesSpec(holding=[4548], models=Inv.TREX)])
    yield _backup_power("T", addresses=[ModbusAddressesSpec(holding=[4552], models=Inv.TREX)])

    def _grid_power(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> Iterable[EntityFactory]:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        yield ModbusSensorDescription(
            key=f"grid_power{key_suffix}",
            addresses=addresses,
            name=f"Grid Power{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:transmission-tower",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
        yield ModbusSensorDescription(
            key=f"grid_power_export{key_suffix}",
            addresses=addresses,
            name=f"Grid Power Export{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:transmission-tower-import",
            scale=scale,
            round_to=0.01,
            post_process=lambda v: abs(v) if v < 0 else 0,
            validate=[Range(0, 100)],
        )
        yield ModbusSensorDescription(
            key=f"grid_power_import{key_suffix}",
            addresses=addresses,
            name=f"Grid Power Import{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:transmission-tower-export",
            scale=scale,
            round_to=0.01,
            post_process=lambda v: v if v > 0 else 0,
            validate=[Range(0, 100)],
        )

    yield from _grid_power(
        phase=None,
        scale=0.001,
        addresses=[
            ModbusAddressesSpec(holding=[4502, 4501], models=Inv.TREX),
        ],
    )

    def _load_power(phase: str | None, *, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""
        return ModbusSensorDescription(
            key=f"load_power{key_suffix}",
            addresses=addresses,
            name=f"Load Power{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:home-lightning-bolt-outline",
            scale=0.001,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )

    yield _load_power(phase=None, addresses=[ModbusAddressesSpec(holding=[4504, 4503], models=Inv.TREX)])


def _inverter_entities() -> Iterable[EntityFactory]:
    def _battery_power(index: int | None, addresses: list[ModbusAddressesSpec]) -> Iterable[ModbusSensorDescription]:
        key_suffix = f"_{index}" if index is not None else ""
        name_infix = f" {index}" if index is not None else ""
        yield ModbusSensorDescription(
            key=f"battery_power{key_suffix}",
            addresses=addresses,
            name=f"Battery{name_infix} Power",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            scale=0.001,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
        yield ModbusSensorDescription(
            key=f"battery_power_discharge{key_suffix}",
            addresses=addresses,
            name=f"Battery{name_infix} Power Discharge",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:battery-arrow-down-outline",
            scale=0.001,
            round_to=0.01,
            post_process=lambda v: abs(v) if v < 0 else 0,
            validate=[Range(0, 100)],
        )
        yield ModbusSensorDescription(
            key=f"battery_power_charge{key_suffix}",
            addresses=addresses,
            name=f"Battery{name_infix} Power Charge",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:battery-arrow-up-outline",
            scale=0.001,
            round_to=0.01,
            post_process=lambda v: v if v > 0 else 0,
            validate=[Range(0, 100)],
        )

    yield from _battery_power(
        index=None,
        addresses=[
            ModbusAddressesSpec(holding=[4367], models=Inv.TREX),
        ],
    )

    yield ModbusSensorDescription(
        key="inverter_temperature",
        addresses=[
            ModbusAddressesSpec(holding=[4426], models=Inv.TREX),
        ],
        name="Inverter Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°C",
        scale=0.1,
        round_to=0.5,
        validate=[Range(0, 100)],
    )
    yield ModbusSensorDescription(
        key="ambient_temperature",
        addresses=[
            ModbusAddressesSpec(holding=[4427], models=Inv.TREX),
        ],
        name="Ambient Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°C",
        scale=0.1,
        round_to=0.5,
        validate=[Range(0, 100)],
    )

    def _inverter_fault_code(addresses: list[ModbusAddressesSpec], fault_set: FaultSet) -> EntityFactory:
        return ModbusFaultSensorDescription(
            key="inverter_fault_code",
            addresses=addresses,
            fault_set=fault_set,
            name="Inverter Fault Code",
            icon="mdi:alert-circle-outline",
        )

    yield _inverter_fault_code(
        addresses=[
            # These addresses are correct for the KH, but the fault codes are not
            ModbusAddressesSpec(input=[11061, 11062, 11064, 11065, 11066, 11067, 11068], models=Inv.H1_G1),
            ModbusAddressesSpec(
                holding=[31031, 31032, 31034, 31035, 31036, 31037, 31038], models=Inv.H1_G1 | Inv.H1_LAN
            ),
            ModbusAddressesSpec(holding=[31044, 31045, 31047, 31048, 31049, 31050, 31051], models=Inv.H3_SET),
        ],
        fault_set=STANDARD_FAULTS,
    )
    yield _inverter_fault_code(
        addresses=[
            ModbusAddressesSpec(holding=[4615], models=Inv.TREX),
        ],
        fault_set=TREX_FAULTS,
    )

    yield ModbusInverterStateSensorDescription(
        key="inverter_state",
        address=[
            ModbusAddressSpec(holding=4353, models=Inv.TREX),
        ],
        name="Inverter State",
        states=TREX_INVERTER_STATES,
    )
    yield ModbusG2InverterStateSensorDescription(
        key="inverter_state",
        addresses=[
            ModbusAddressesSpec(holding=[39063, 39065], models=Inv.H1_G2_SET | Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Inverter State",
    )

    def _pv_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="pv_energy_total",
            addresses=addresses,
            name="PV Energy Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:solar-power",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _pv_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4441, 4440, 4439, 4438], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _battery_energy_charge_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="battery_energy_charge_total",
            addresses=addresses,
            name="Battery Energy Charge Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:battery-arrow-up-outline",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _battery_energy_charge_total(
        addresses=[
            ModbusAddressesSpec(holding=[4481, 4480, 4479, 4478], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _battery_energy_discharge_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="battery_energy_discharge_total",
            addresses=addresses,
            name="Battery Energy Discharge Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:battery-arrow-down-outline",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _battery_energy_discharge_total(
        addresses=[
            ModbusAddressesSpec(holding=[4491, 4490, 4489, 4488], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _grid_energy_export_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="grid_energy_export_total",
            addresses=addresses,
            name="Grid Energy Export Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:transmission-tower-import",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _grid_energy_export_total(
        addresses=[
            ModbusAddressesSpec(holding=[4471, 4470, 4469, 4468], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _grid_energy_import_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="grid_energy_import_total",
            addresses=addresses,
            name="Grid Energy Import Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:transmission-tower-export",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _grid_energy_import_total(
        addresses=[
            ModbusAddressesSpec(holding=[4461, 4460, 4459, 4458], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _input_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="input_energy_total",
            addresses=addresses,
            name="Backup Energy Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:import",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _input_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4461, 4460, 4459, 4458], models=Inv.GWETP),
        ],
        scale=0.01,
    )

    def _load_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="load_energy_total",
            addresses=addresses,
            name="Load Energy Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:home-lightning-bolt-outline",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )

    yield _load_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4451, 4450, 4449, 4448], models=Inv.TREX),
        ],
        scale=0.001,
    )


def _bms_entities() -> Iterable[EntityFactory]:
    def _inner(
        index: int | None,
        bms_connect_state_address: list[ModbusAddressSpec],
        battery_voltage: list[ModbusAddressesSpec],
        battery_current: list[ModbusAddressesSpec],
        battery_soc: list[ModbusAddressesSpec],
        battery_soh: list[ModbusAddressesSpec],
        battery_temp: list[ModbusAddressesSpec],
        bms_cell_temp_high: list[ModbusAddressesSpec],
        bms_cell_temp_low: list[ModbusAddressesSpec],
        bms_cell_mv_high: list[ModbusAddressesSpec],
        bms_cell_mv_low: list[ModbusAddressesSpec],
        bms_kwh_remaining: list[ModbusAddressesSpec],
    ) -> Iterable[EntityFactory]:
        key_suffix = f"_{index}" if index is not None else ""
        name_infix = f" {index}" if index is not None else ""

        yield ModbusSensorDescription(
            key=f"battery_voltage{key_suffix}",
            addresses=battery_voltage,
            name=f"Battery{name_infix} Voltage",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="V",
            scale=0.01,
            round_to=0.01,
            validate=[Min(0)],
        )
        yield ModbusSensorDescription(
            key=f"battery_current{key_suffix}",
            addresses=battery_current,
            name=f"Battery{name_infix} Current",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="A",
            scale=0.1,
            round_to=1,
            validate=[Range(-200, 200)],
        )
        yield ModbusBatterySensorDescription(
            key=f"battery_soc{key_suffix}",
            addresses=battery_soc,
            bms_connect_state_address=bms_connect_state_address,
            name=f"Battery{name_infix} SoC",
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="%",
            signed=False,
            scale=0.1,
            round_to=1,
            validate=[Range(0, 100)],
        )
        yield ModbusBatterySensorDescription(
            key=f"battery_soh{key_suffix}",
            addresses=battery_soh,
            bms_connect_state_address=bms_connect_state_address,
            name=f"Battery{name_infix} SoH",
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="%",
            signed=False,
            validate=[Range(0, 100)],
        )
        yield ModbusBatterySensorDescription(
            key=f"battery_temp{key_suffix}",
            addresses=battery_temp,
            bms_connect_state_address=bms_connect_state_address,
            name=f"Battery{name_infix} Temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="°C",
            scale=0.1,
            validate=[Range(0, 100)],
        )
        yield ModbusBatterySensorDescription(
            key=f"bms_cell_temp_high{key_suffix}",
            addresses=bms_cell_temp_high,
            bms_connect_state_address=bms_connect_state_address,
            name=f"BMS{name_infix} Cell Temp High",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="°C",
            scale=0.1,
            validate=[Range(0, 100)],
        )
        yield ModbusBatterySensorDescription(
            key=f"bms_cell_temp_low{key_suffix}",
            addresses=bms_cell_temp_low,
            bms_connect_state_address=bms_connect_state_address,
            name=f"BMS{name_infix} Cell Temp Low",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="°C",
            scale=0.1,
            validate=[Range(0, 100)],
        )
        yield ModbusBatterySensorDescription(
            key=f"bms_cell_mv_high{key_suffix}",
            addresses=bms_cell_mv_high,
            bms_connect_state_address=bms_connect_state_address,
            name=f"BMS{name_infix} Cell mV High",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="mV",
            signed=False,
            round_to=10,
            validate=[Min(0)],
        )
        yield ModbusBatterySensorDescription(
            key=f"bms_cell_mv_low{key_suffix}",
            addresses=bms_cell_mv_low,
            bms_connect_state_address=bms_connect_state_address,
            name=f"BMS{name_infix} Cell mV Low",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="mV",
            signed=False,
            round_to=10,
            validate=[Min(0)],
        )
        yield ModbusBatterySensorDescription(
            key=f"bms_kwh_remaining{key_suffix}",
            addresses=bms_kwh_remaining,
            bms_connect_state_address=bms_connect_state_address,
            name=f"BMS{name_infix} kWh Remaining",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            scale=0.01,
            signed=False,
            validate=[Min(0)],
        )

    yield from _inner(
        index=None,
        bms_connect_state_address=BMS_CONNECT_STATE_ADDRESS,
        battery_voltage=[
            ModbusAddressesSpec(holding=[4621], models=Inv.TREX),
        ],
        battery_current=[
            ModbusAddressesSpec(holding=[4620], models=Inv.TREX),
        ],
        battery_soc=[
            ModbusAddressesSpec(holding=[4624], models=Inv.TREX),
        ],
        battery_soh=[
            ModbusAddressesSpec(holding=[31090], models=Inv.H3_180),
        ],
        battery_temp=[
            ModbusAddressesSpec(holding=[31037], models=Inv.H3_SET),
        ],
        bms_cell_temp_high=[
            ModbusAddressesSpec(holding=[31102], models=Inv.H3_180),
        ],
        bms_cell_temp_low=[
            ModbusAddressesSpec(holding=[31103], models=Inv.H3_180),
        ],
        bms_cell_mv_high=[
            ModbusAddressesSpec(holding=[31134], models=Inv.H3_180),
        ],
        bms_cell_mv_low=[
            ModbusAddressesSpec(holding=[31135], models=Inv.H3_180),
        ],
        bms_kwh_remaining=[
            ModbusAddressesSpec(holding=[31123], models=Inv.H3_180),
        ],
    )
    yield from _inner(
        index=1,
        bms_connect_state_address=[ModbusAddressSpec(holding=37002, models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_voltage=[ModbusAddressesSpec(holding=[37609], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_current=[ModbusAddressesSpec(holding=[37610], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soc=[ModbusAddressesSpec(holding=[37612], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soh=[ModbusAddressesSpec(holding=[37624], models=Inv.H3_SMART)],
        battery_temp=[ModbusAddressesSpec(holding=[37611], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_temp_high=[ModbusAddressesSpec(holding=[37617], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_temp_low=[ModbusAddressesSpec(holding=[37618], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_mv_high=[ModbusAddressesSpec(holding=[37619], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_mv_low=[ModbusAddressesSpec(holding=[37620], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_kwh_remaining=[ModbusAddressesSpec(holding=[37632], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
    )
    yield from _inner(
        index=2,
        bms_connect_state_address=[ModbusAddressSpec(holding=37700, models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_voltage=[ModbusAddressesSpec(holding=[38307], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_current=[ModbusAddressesSpec(holding=[38308], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soc=[ModbusAddressesSpec(holding=[38310], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soh=[ModbusAddressesSpec(holding=[38322], models=Inv.H3_SMART)],
        battery_temp=[ModbusAddressesSpec(holding=[38309], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_temp_high=[ModbusAddressesSpec(holding=[38315], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_temp_low=[ModbusAddressesSpec(holding=[38316], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_mv_high=[ModbusAddressesSpec(holding=[38317], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_cell_mv_low=[ModbusAddressesSpec(holding=[38318], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bms_kwh_remaining=[ModbusAddressesSpec(holding=[38330], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
    )


def _configuration_entities() -> Iterable[EntityFactory]:
    # Work Mode
    yield ModbusWorkModeSelectDescription(
        key="work_mode",
        address=[
            ModbusAddressSpec(holding=8451, models=Inv.TREX),
        ],
        name="Work Mode",
        options_map={0: "General", 1: "Backup", 2: "Impex"},
    )

    # Impex mode
    yield ModbusWorkModeSelectDescription(
        key="impex_mode",
        address=[
            ModbusAddressSpec(holding=8568, models=Inv.TREX),
        ],
        name="Impex Mode",
        options_map={0: "Disable", 1: "Charge", 2: "Discharge"},
    )
    # Min SoC (Off Grid)
    yield ModbusSensorDescription(
        key="battery_battery_min_soc_impex",
        addresses=[
            ModbusAddressesSpec(holding=[8575], models=Inv.GWETP),
        ],
        name="Battery Min SoC Impex",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
        native_unit_of_measurement="%",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="battery_battery_min_soc_impex",
        address=[
            ModbusAddressSpec(holding=8575, models=Inv.TREX),
        ],
        name="Battery Min SoC Impex",
        mode=NumberMode.BOX,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        device_class=NumberDeviceClass.BATTERY,
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="battery_power_impex",
        address=[
            ModbusAddressSpec(holding=8576, models=Inv.TREX),
        ],
        name="Battery Power Impex",
        mode=NumberMode.BOX,
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        native_unit_of_measurement="kW",
        scale=0.001,
        validate=[Range(0, 10)],
    )

    # Max Charge Current
    yield ModbusSensorDescription(
        key="battery_max_charge_current",
        addresses=[
            ModbusAddressesSpec(holding=[8493], models=Inv.TREX),
        ],
        name="Battery Max Charge Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        round_to=1,
        validate=[Range(0, 200)],
    )
    yield ModbusNumberDescription(
        key="battery_max_charge_current",
        address=[
            ModbusAddressSpec(holding=8493, models=Inv.TREX),
        ],
        name="Battery Max Charge Current",
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=0,
        native_max_value=200,
        native_step=0.1,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 200)],
    )

    # Max Discharge Current
    yield ModbusSensorDescription(
        key="battery_max_discharge_current",
        addresses=[
            ModbusAddressesSpec(holding=[8494], models=Inv.TREX),
        ],
        name="Battery Max Discharge Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        round_to=1,
        validate=[Range(0, 200)],
    )
    yield ModbusNumberDescription(
        key="battery_max_discharge_current",
        address=[
            ModbusAddressSpec(holding=8494, models=Inv.TREX),
        ],
        name="Battery Max Discharge Current",
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=0,
        native_max_value=200,
        native_step=0.1,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 200)],
    )

    # Min SoC (Off Grid)
    yield ModbusSensorDescription(
        key="battery_min_soc",
        addresses=[
            ModbusAddressesSpec(holding=[8491], models=Inv.TREX),
        ],
        name="Battery Min SoC OffGrid",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
        native_unit_of_measurement="%",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="battery_min_soc",
        address=[
            ModbusAddressSpec(holding=8491, models=Inv.TREX),
        ],
        name="Battery Min SoC OffGrid",
        mode=NumberMode.BOX,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        device_class=NumberDeviceClass.BATTERY,
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )

    # Min SoC (On Grid)
    yield ModbusSensorDescription(
        key="battery_min_soc_on_grid",
        addresses=[
            ModbusAddressesSpec(holding=[8490], models=Inv.TREX),
        ],
        name="Battery Min SoC OnGrid",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="battery_min_soc_on_grid",
        address=[
            ModbusAddressSpec(holding=8490, models=Inv.TREX),
        ],
        name="Battery Min SoC OnGrid",
        mode=NumberMode.BOX,
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        device_class=NumberDeviceClass.BATTERY,
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )


ENTITIES: list[EntityFactory] = sorted(
    itertools.chain(
        _version_entities(),
        _pv_entities(),
        _h3_current_voltage_power_entities(),
        _inverter_entities(),
        _bms_entities(),
        _configuration_entities(),
        (description for x in CHARGE_PERIODS for description in x.entity_descriptions),
        REMOTE_CONTROL_DESCRIPTION.entity_descriptions,
    ),
    key=lambda x: x.depends_on_other_entities,
)
