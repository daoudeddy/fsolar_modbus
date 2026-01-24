"""Holds all entity descriptions for all entities across all inverters."""

import itertools
from typing import Iterable

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfTime

from custom_components.fsolar_modbus.entities.base_validator import BaseValidator

from ..common.register_types import Inv
from ..common.register_types import RegisterType
from .charge_period_descriptions import CHARGE_PERIODS
from .entity_factory import EntityFactory
from .inverter_model_spec import EntitySpec
from .inverter_model_spec import ModbusAddressesSpec
from .inverter_model_spec import ModbusAddressSpec
from .modbus_battery_sensor import ModbusBatterySensorDescription
from .modbus_fault_sensor import H3_PRO_KH_133_FAULTS
from .modbus_fault_sensor import STANDARD_FAULTS
from .modbus_fault_sensor import FaultSet
from .modbus_fault_sensor import ModbusFaultSensorDescription
from .modbus_integration_sensor import ModbusIntegrationSensorDescription
from .modbus_inverter_state_sensor import H1_INVERTER_STATES
from .modbus_inverter_state_sensor import KH_INVERTER_STATES
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

    def _pv_energy_total(key: str, models: list[EntitySpec], name: str, source_entity: str) -> EntityFactory:
        return ModbusIntegrationSensorDescription(
            key=key,
            models=models,
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement="kWh",
            integration_method="left",
            name=name,
            source_entity=source_entity,
            unit_time=UnitOfTime.HOURS,
            icon="mdi:solar-power-variant-outline",
        )

    yield _pv_voltage(
        key="pv1_voltage",
        addresses=[
            ModbusAddressesSpec(input=[11000], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[31000], models=Inv.H1_G1 | Inv.H1_LAN | Inv.KH_PRE133 | Inv.H3_SET),
            ModbusAddressesSpec(holding=[39070], models=Inv.H1_G2_SET | Inv.KH_133 | Inv.H3_PRO_SET | Inv.H3_SMART),
            ModbusAddressesSpec(holding=[35103], models=Inv.GWETP),
            ModbusAddressesSpec(holding=[4375], models=Inv.TREX),
        ],
        name="PV1 Voltage",
    )
    yield _pv_current(
        key="pv1_current",
        addresses=[
            ModbusAddressesSpec(input=[11001], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[31001], models=Inv.H1_G1 | Inv.H1_LAN | Inv.KH_PRE133 | Inv.H3_SET),
            ModbusAddressesSpec(holding=[4376], models=Inv.TREX),
        ],
        name="PV1 Current",
        scale=0.1,
    )
    yield _pv_current(
        key="pv1_current",
        addresses=[
            ModbusAddressesSpec(holding=[39071], models=Inv.H1_G2_SET | Inv.KH_133 | Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="PV1 Current",
        scale=0.01,
    )
    yield _pv_power(
        key="pv1_power",
        addresses=[
            ModbusAddressesSpec(input=[11002], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[31002], models=Inv.H1_G1 | Inv.H1_LAN | Inv.KH_PRE133 | Inv.H3_SET),
            # This is techincally a 32-bit register on the G2, but it doesn't appear to actually write the upper word,
            # which means that negative values are represented incorrectly (as 0x0000FFFF etc)
            ModbusAddressesSpec(holding=[39280], models=Inv.H1_G2_SET),
            ModbusAddressesSpec(holding=[39280, 39279], models=Inv.KH_133 | Inv.H3_PRO_SET | Inv.H3_SMART),
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
            ModbusAddressesSpec(input=[11004], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[31004], models=Inv.H1_G1 | Inv.H1_LAN | Inv.KH_PRE133 | Inv.H3_SET),
            ModbusAddressesSpec(holding=[4379], models=Inv.TREX),
        ],
        name="PV2 Current",
        scale=0.1,
    )
    yield _pv_current(
        key="pv2_current",
        addresses=[
            ModbusAddressesSpec(holding=[39073], models=Inv.H1_G2_SET | Inv.KH_133 | Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="PV2 Current",
        scale=0.01,
    )
    yield _pv_power(
        key="pv2_power",
        addresses=[
            ModbusAddressesSpec(input=[11005], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[31005], models=Inv.H1_G1 | Inv.H1_LAN | Inv.KH_PRE133 | Inv.H3_SET),
            # This is techincally a 32-bit register on the G2, but it doesn't appear to actually write the upper word,
            # which means that negative values are represented incorrectly (as 0x0000FFFF etc)
            ModbusAddressesSpec(holding=[39282], models=Inv.H1_G2_SET),
            ModbusAddressesSpec(holding=[39282, 39281], models=Inv.KH_133 | Inv.H3_PRO_SET | Inv.H3_SMART),
            ModbusAddressesSpec(holding=[4380], models=Inv.TREX),
        ],
        name="PV2 Power",
    )
    yield ModbusLambdaSensorDescription(
        key="pv_power_now",
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

    def _inv_current(phase: str, addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"inv_current_{phase}",
            addresses=addresses,
            name=f"Inverter Current {phase}",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="A",
            scale=scale,
            round_to=1,
            validate=[Range(0, 100)],
        )
    def _inv_current_set(
        r_addresses: list[ModbusAddressesSpec],
        s_addresses: list[ModbusAddressesSpec],
        t_addresses: list[ModbusAddressesSpec],
        scale: float,
    ) -> Iterable[EntityFactory]:
        yield _inv_current("R", addresses=r_addresses, scale=scale)
        yield _inv_current("S", addresses=s_addresses, scale=scale)
        yield _inv_current("T", addresses=t_addresses, scale=scale)
    yield from _inv_current_set(
        r_addresses=[ModbusAddressesSpec(holding=[4362], models=Inv.TREX)],
        s_addresses=[ModbusAddressesSpec(holding=[4385], models=Inv.TREX)],
        t_addresses=[ModbusAddressesSpec(holding=[4389], models=Inv.TREX)],
        scale=0.1,
    )

    def _inv_power(phase: str | None, addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""
        return ModbusSensorDescription(
            key=f"inv_power{key_suffix}",
            addresses=addresses,
            name=f"Inverter Power{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
    yield _inv_power(
        "R",
        addresses=[
            ModbusAddressesSpec(holding=[4364], models=Inv.TREX),
        ],
        scale=0.001,
    )
    yield _inv_power(
        "S",
        addresses=[
            ModbusAddressesSpec(holding=[4387], models=Inv.TREX),
        ],
        scale=0.001,
    )
    yield _inv_power(
        "T",
        addresses=[
            ModbusAddressesSpec(holding=[4391], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _eps_rvolt(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"eps_rvolt_{phase}",
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
    yield _eps_rvolt("R", addresses=[ModbusAddressesSpec(holding=[39201], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _eps_rvolt("S", addresses=[ModbusAddressesSpec(holding=[39202], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _eps_rvolt("T", addresses=[ModbusAddressesSpec(holding=[39203], models=Inv.H3_PRO_SET | Inv.H3_SMART)])

    def _eps_rcurrent(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"eps_rcurrent_{phase}",
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
    yield _eps_rcurrent("R", addresses=[ModbusAddressesSpec(holding=[39205, 39204], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _eps_rcurrent("S", addresses=[ModbusAddressesSpec(holding=[39207, 39206], models=Inv.H3_PRO_SET | Inv.H3_SMART)])
    yield _eps_rcurrent("T", addresses=[ModbusAddressesSpec(holding=[39209, 39208], models=Inv.H3_PRO_SET | Inv.H3_SMART)])

    def _eps_power(phase: str, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        return ModbusSensorDescription(
            key=f"eps_power_{phase}",
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
    yield _eps_power("R",addresses=[ModbusAddressesSpec(holding=[4531], models=Inv.TREX)])
    yield _eps_power("S",addresses=[ModbusAddressesSpec(holding=[4548], models=Inv.TREX)])
    yield _eps_power("T",addresses=[ModbusAddressesSpec(holding=[4552], models=Inv.TREX)])

    def _grid_ct(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> Iterable[EntityFactory]:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        yield ModbusSensorDescription(
            key=f"grid_ct{key_suffix}",
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
            key=f"feed_in{key_suffix}",
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
            key=f"grid_consumption{key_suffix}",
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
    yield from _grid_ct(
        phase=None,
        scale=0.001,
        addresses=[
            ModbusAddressesSpec(holding=[4502, 4501], models=Inv.TREX),
        ],
    )

    def _grid_ct_reactive(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        return ModbusSensorDescription(
            key=f"grid_ct_reactive{key_suffix}",
            addresses=addresses,
            name=f"Grid CT (Reactive){name_suffix}",
            entity_registry_enabled_default=False,
            # REACTIVE_POWER only supports var, not kvar
            # device_class=SensorDeviceClass.REACTIVE_POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kvar",
            icon="mdi:meter-electric-outline",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
    def _grid_ct_reactive_set(
        addresses: list[ModbusAddressesSpec],
        r_addresses: list[ModbusAddressesSpec],
        s_addresses: list[ModbusAddressesSpec],
        t_addresses: list[ModbusAddressesSpec],
        scale: float,
    ) -> Iterable[EntityFactory]:
        yield _grid_ct_reactive(phase=None, addresses=addresses, scale=scale)
        yield _grid_ct_reactive(phase="R", addresses=r_addresses, scale=scale)
        yield _grid_ct_reactive(phase="S", addresses=s_addresses, scale=scale)
        yield _grid_ct_reactive(phase="T", addresses=t_addresses, scale=scale)
    yield from _grid_ct_reactive_set(
        addresses=[ModbusAddressesSpec(holding=[38823, 38822], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        r_addresses=[ModbusAddressesSpec(holding=[38825, 38824], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        s_addresses=[ModbusAddressesSpec(holding=[38827, 38826], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        t_addresses=[ModbusAddressesSpec(holding=[38829, 38828], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        scale=0.0001,
    )

    def _grid_ct_apparent(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        return ModbusSensorDescription(
            key=f"grid_ct_apparent{key_suffix}",
            addresses=addresses,
            name=f"Grid CT (Apparent){name_suffix}",
            entity_registry_enabled_default=False,
            # APPARENT_POWER only supports VA, not kVA
            # device_class=SensorDeviceClass.APPARENT_POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kVA",
            icon="mdi:meter-electric-outline",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
    def _grid_ct_apparent_set(
        addresses: list[ModbusAddressesSpec],
        r_addresses: list[ModbusAddressesSpec],
        s_addresses: list[ModbusAddressesSpec],
        t_addresses: list[ModbusAddressesSpec],
        scale: float,
    ) -> Iterable[EntityFactory]:
        yield _grid_ct_apparent(phase=None, addresses=addresses, scale=scale)
        yield _grid_ct_apparent(phase="R", addresses=r_addresses, scale=scale)
        yield _grid_ct_apparent(phase="S", addresses=s_addresses, scale=scale)
        yield _grid_ct_apparent(phase="T", addresses=t_addresses, scale=scale)
    yield from _grid_ct_apparent_set(
        addresses=[ModbusAddressesSpec(holding=[38831, 38830], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        r_addresses=[ModbusAddressesSpec(holding=[38833, 38832], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        s_addresses=[ModbusAddressesSpec(holding=[38835, 38834], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        t_addresses=[ModbusAddressesSpec(holding=[38837, 38836], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        scale=0.0001,
    )

    def _grid_ct_power_factor(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> EntityFactory:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        return ModbusSensorDescription(
            key=f"grid_ct_pf{key_suffix}",
            addresses=addresses,
            name=f"Grid CT Power Factor{name_suffix}",
            entity_registry_enabled_default=False,
            # device_class=SensorDeviceClass.POWER_FACTOR,
            state_class=SensorStateClass.MEASUREMENT,
            # Power factor is a ratio with no unit. Supposedly gain 1000, but comes out as .01
            icon="mdi:meter-electric-outline",
            scale=scale,
            round_to=0.001,
            validate=[Range(-1, 1)],
        )
    def _grid_ct_power_factor_set(
        addresses: list[ModbusAddressesSpec],
        r_addresses: list[ModbusAddressesSpec],
        s_addresses: list[ModbusAddressesSpec],
        t_addresses: list[ModbusAddressesSpec],
        scale: float,
    ) -> Iterable[EntityFactory]:
        yield _grid_ct_power_factor(phase=None, addresses=addresses, scale=scale)
        yield _grid_ct_power_factor(phase="R", addresses=r_addresses, scale=scale)
        yield _grid_ct_power_factor(phase="S", addresses=s_addresses, scale=scale)
        yield _grid_ct_power_factor(phase="T", addresses=t_addresses, scale=scale)
    yield from _grid_ct_power_factor_set(
        addresses=[ModbusAddressesSpec(holding=[38839, 38838], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        r_addresses=[ModbusAddressesSpec(holding=[38841, 38840], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        s_addresses=[ModbusAddressesSpec(holding=[38843, 38842], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        t_addresses=[ModbusAddressesSpec(holding=[38845, 38844], models=Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122)],
        scale=0.00001,
    )

    def _ct2_meter(phase: str | None, scale: float, addresses: list[ModbusAddressesSpec]) -> ModbusSensorDescription:
        key_suffix = f"_{phase}" if phase is not None else ""
        name_suffix = f" {phase}" if phase is not None else ""

        return ModbusSensorDescription(
            key=f"ct2_meter{key_suffix}",
            addresses=addresses,
            name=f"CT2 Meter{name_suffix}",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kW",
            icon="mdi:meter-electric-outline",
            scale=scale,
            round_to=0.01,
            validate=[Range(-100, 100)],
        )
    yield _ct2_meter(
        phase=None,
        scale=0.0001,
        addresses=[ModbusAddressesSpec(holding=[38915, 38914], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
    )
    yield _ct2_meter(
        "R", scale=0.0001, addresses=[ModbusAddressesSpec(holding=[38917, 38916], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
    )
    yield _ct2_meter(
        "S", scale=0.0001, addresses=[ModbusAddressesSpec(holding=[38919, 38918], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
    )
    yield _ct2_meter(
        "T", scale=0.0001, addresses=[ModbusAddressesSpec(holding=[38921, 38920], models=Inv.H3_PRO_SET | Inv.H3_SMART)]
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
    def _invbatpower(index: int | None, addresses: list[ModbusAddressesSpec]) -> Iterable[ModbusSensorDescription]:
        key_suffix = f"_{index}" if index is not None else ""
        name_infix = f" {index}" if index is not None else ""
        yield ModbusSensorDescription(
            key=f"invbatpower{key_suffix}",
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
            key=f"battery_discharge{key_suffix}",
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
            key=f"battery_charge{key_suffix}",
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
    yield from _invbatpower(
        index=None,
        addresses=[
            ModbusAddressesSpec(holding=[4367], models=Inv.TREX),
        ],
    )

    yield ModbusSensorDescription(
        key="rfreq",
        addresses=[
            ModbusAddressesSpec(input=[11014], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31009], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[31015], models=Inv.H3_SET),
            ModbusAddressesSpec(holding=[38847, 38846], models=Inv.H3_PRO_PRE122),
            ModbusAddressesSpec(holding=[39139], models=Inv.H3_PRO_122),
        ],
        entity_registry_enabled_default=False,
        name="Grid Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Hz",
        scale=0.01,
        round_to=0.1,
        signed=False,
        validate=[Range(0, 60)],
    )
    yield ModbusSensorDescription(
        key="eps_frequency",
        addresses=[
            ModbusAddressesSpec(input=[11020], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31013], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[31025], models=Inv.H3_SET),
        ],
        entity_registry_enabled_default=False,
        name="Backup Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Hz",
        scale=0.01,
        round_to=0.1,
        signed=False,
        validate=[Range(0, 60)],
    )
    yield ModbusSensorDescription(
        key="invtemp",
        addresses=[
            ModbusAddressesSpec(input=[11024], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31018], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[31032], models=Inv.H3_SET),
            ModbusAddressesSpec(holding=[39141], models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Inverter Temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°C",
        scale=0.1,
        round_to=0.5,
        validate=[Range(0, 100)],
    )
    yield ModbusSensorDescription(
        key="ambtemp",
        addresses=[
            ModbusAddressesSpec(input=[11025], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31019], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[31033], models=Inv.H3_SET),
        ],
        name="Ambient Temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°C",
        scale=0.1,
        round_to=0.5,
        validate=[Range(0, 100)],
    )
    yield ModbusBatterySensorDescription(
        key="bms_charge_rate",
        addresses=[
            ModbusAddressesSpec(input=[11041], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31025], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
        ],
        entity_registry_enabled_default=False,
        bms_connect_state_address=BMS_CONNECT_STATE_ADDRESS,
        name="BMS Charge Rate",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        signed=False,
        validate=[Range(0, 100)],
    )
    yield ModbusBatterySensorDescription(
        key="bms_discharge_rate",
        addresses=[
            ModbusAddressesSpec(input=[11042], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31026], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
        ],
        entity_registry_enabled_default=False,
        bms_connect_state_address=BMS_CONNECT_STATE_ADDRESS,
        name="BMS Discharge Rate",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        signed=False,
        validate=[Range(0, 100)],
    )
    yield ModbusBatterySensorDescription(
        key="bms_cycle_count",
        addresses=[
            ModbusAddressesSpec(input=[11048], models=Inv.H1_G1 | Inv.KH_PRE119),
        ],
        bms_connect_state_address=BMS_CONNECT_STATE_ADDRESS,
        name="BMS Cycle Count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:counter",
        signed=False,
        validate=[Min(0)],
    )
    yield ModbusBatterySensorDescription(
        key="bms_watthours_total",
        addresses=[
            ModbusAddressesSpec(input=[11049], models=Inv.H1_G1 | Inv.KH_PRE119),
        ],
        bms_connect_state_address=BMS_CONNECT_STATE_ADDRESS,
        entity_registry_enabled_default=False,
        name="BMS Energy Throughput",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="kWh",
        scale=0.001,
        round_to=1,
        signed=False,
        validate=[Min(0)],
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
        # We don't map Fault Code 3, as it's unused
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
            ModbusAddressesSpec(
                holding=[39067, 39068, 39069], models=Inv.H3_PRO_SET | Inv.H3_SMART | Inv.H1_G2_144 | Inv.KH_133
            ),
        ],
        fault_set=H3_PRO_KH_133_FAULTS,
    )

    yield ModbusInverterStateSensorDescription(
        key="inverter_state",
        address=[
            ModbusAddressSpec(input=11056, models=Inv.H1_G1),
            ModbusAddressSpec(holding=31027, models=Inv.H1_G1 | Inv.H1_LAN),
        ],
        name="Inverter State",
        states=H1_INVERTER_STATES,
    )
    yield ModbusInverterStateSensorDescription(
        key="inverter_state",
        address=[
            ModbusAddressSpec(input=11056, models=Inv.KH_PRE119),
            ModbusAddressSpec(holding=31027, models=Inv.KH_PRE133 | Inv.KH_133),
        ],
        name="Inverter State",
        states=KH_INVERTER_STATES,
    )
    yield ModbusG2InverterStateSensorDescription(
        key="inverter_state",
        addresses=[
            ModbusAddressesSpec(holding=[39063, 39065], models=Inv.H1_G2_SET | Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Inverter State",
    )
    yield ModbusSensorDescription(
        key="state_code",
        addresses=[
            ModbusAddressesSpec(holding=[31041], models=Inv.H3_SET),
        ],
        name="Inverter State Code",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def _solar_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="solar_energy_total",
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
    yield _solar_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4441, 4440, 4439, 4438], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _battery_charge_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="battery_charge_total",
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
    yield _battery_charge_total(
        addresses=[
            ModbusAddressesSpec(holding=[4481, 4480, 4479, 4478], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _battery_discharge_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="battery_discharge_total",
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
    yield _battery_discharge_total(
        addresses=[
            ModbusAddressesSpec(holding=[4491, 4490, 4489, 4488], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _grid_export_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="grid_export_energy_total",
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
    yield _grid_export_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4471, 4470, 4469, 4468], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _grid_import_energy_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="grid_import_energy_total",
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
    yield _grid_import_energy_total(
        addresses=[
            ModbusAddressesSpec(holding=[4461, 4460, 4459, 4458], models=Inv.TREX),
        ],
        scale=0.001,
    )

    def _total_yield_total(addresses: list[ModbusAddressesSpec], scale: float) -> EntityFactory:
        return ModbusSensorDescription(
            key="total_yield_total",
            addresses=addresses,
            name="Inverter Energy PV Total",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL,
            native_unit_of_measurement="kWh",
            icon="mdi:export",
            scale=scale,
            round_to=1,
            signed=False,
            validate=[Min(0)],
        )
    yield _total_yield_total(
        addresses=[
            ModbusAddressesSpec(input=[11085, 11084], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[32016, 32015], models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[39622, 39621], models=Inv.H3_PRO_PRE122),
        ],
        scale=0.1,
    )
    yield _total_yield_total(
        addresses=[
            ModbusAddressesSpec(holding=[39622, 39621], models=Inv.H3_SMART | Inv.H3_PRO_SET & ~Inv.H3_PRO_PRE122),
        ],
        scale=0.01,
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
        batvolt: list[ModbusAddressesSpec],
        bat_current: list[ModbusAddressesSpec],
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
            key=f"batvolt{key_suffix}",
            addresses=batvolt,
            name=f"Battery{name_infix} Voltage",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="V",
            scale=0.01,
            round_to=0.01,
            validate=[Min(0)],
        )
        yield ModbusSensorDescription(
            key=f"bat_current{key_suffix}",
            addresses=bat_current,
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
        batvolt=[
            ModbusAddressesSpec(holding=[4621], models=Inv.TREX),
        ],
        bat_current=[
            ModbusAddressesSpec(holding=[4620], models=Inv.TREX),
        ],
        battery_soc=[
            ModbusAddressesSpec(holding=[4624], models=Inv.TREX),
        ],
        battery_soh=[
            # Temporarily removed, see #756
            # ModbusAddressesSpec(input=[11104], models=Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37624], models=Inv.H1_G2_144 | Inv.KH_133),
            ModbusAddressesSpec(holding=[31090], models=Inv.H3_180),
        ],
        battery_temp=[
            ModbusAddressesSpec(input=[11038], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[31023], models=Inv.H1_G1 | Inv.H1_LAN | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133
            ),
            ModbusAddressesSpec(holding=[31037], models=Inv.H3_SET),
        ],
        bms_cell_temp_high=[
            ModbusAddressesSpec(input=[11043], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37617], models=Inv.H1_G2_144 | Inv.KH_133),
            ModbusAddressesSpec(holding=[31102], models=Inv.H3_180),
        ],
        bms_cell_temp_low=[
            ModbusAddressesSpec(input=[11044], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37618], models=Inv.H1_G2_144 | Inv.KH_133),
            ModbusAddressesSpec(holding=[31103], models=Inv.H3_180),
        ],
        bms_cell_mv_high=[
            ModbusAddressesSpec(input=[11045], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37619], models=Inv.H1_G2_144 | Inv.KH_133),
            ModbusAddressesSpec(holding=[31134], models=Inv.H3_180),
        ],
        bms_cell_mv_low=[
            ModbusAddressesSpec(input=[11046], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37620], models=Inv.H1_G2_144 | Inv.KH_133),
            ModbusAddressesSpec(holding=[31135], models=Inv.H3_180),
        ],
        bms_kwh_remaining=[
            ModbusAddressesSpec(input=[11037], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[37632], models=Inv.H1_G2_SET | Inv.KH_133),
            ModbusAddressesSpec(holding=[31123], models=Inv.H3_180),
        ],
    )
    yield from _inner(
        index=1,
        bms_connect_state_address=[ModbusAddressSpec(holding=37002, models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        batvolt=[ModbusAddressesSpec(holding=[37609], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bat_current=[ModbusAddressesSpec(holding=[37610], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soc=[ModbusAddressesSpec(holding=[37612], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        # Added in H3_PRO v1.25, which hasn't been released yet.
        # See https://github.com/comcowo/fsolar_modbus/pull/775#issuecomment-2656447502
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
        batvolt=[ModbusAddressesSpec(holding=[38307], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        bat_current=[ModbusAddressesSpec(holding=[38308], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        battery_soc=[ModbusAddressesSpec(holding=[38310], models=Inv.H3_PRO_SET | Inv.H3_SMART)],
        # Added in H3_PRO v1.25, which hasn't been released yet.
        # See https://github.com/comcowo/fsolar_modbus/pull/775#issuecomment-2656447502
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
            ModbusAddressSpec(input=41000, models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressSpec(holding=41000, models=Inv.H1_G1 | Inv.KH_PRE133 | Inv.KH_133),
        ],
        name="Work Mode",
        options_map={0: "Self Use", 1: "Feed-in First", 2: "Back-up"},
    )
    yield ModbusWorkModeSelectDescription(
        key="work_mode",
        address=[
            ModbusAddressSpec(holding=49203, models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Work Mode",
        options_map={
            1: "Self Use",
            2: "Feed-in First",
            3: "Back-up",
            4: "Peak Shaving",
        },
    )
    yield ModbusWorkModeSelectDescription(
        key="work_mode",
        address=[
            ModbusAddressSpec(holding=41000, models=Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101),
        ],
        name="Work Mode",
        options_map={0: "Self Use", 1: "Feed-in First", 2: "Back-up", 4: "Peak Shaving"},
    )

    # Max Charge Current
    yield ModbusSensorDescription(
        key="max_charge_current",
        addresses=[
            ModbusAddressesSpec(input=[41007], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(holding=[41007], models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101 | Inv.KH_PRE133 | Inv.KH_133,),
            ModbusAddressesSpec(holding=[46607], models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Max Charge Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 50)],
    )
    yield ModbusNumberDescription(
        key="max_charge_current",
        address=[
            ModbusAddressSpec(input=41007, models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressSpec(holding=41007, models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101 | Inv.KH_PRE133 | Inv.KH_133,),
            ModbusAddressSpec(holding=46607, models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Max Charge Current",
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=0,
        native_max_value=50,
        native_step=0.1,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 50)],
    )
    
    # Max Discharge Current
    yield ModbusSensorDescription(
        key="max_discharge_current",
        addresses=[
            ModbusAddressesSpec(input=[41008], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[41008],
                models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101 | Inv.KH_PRE133 | Inv.KH_133,
            ),
            ModbusAddressesSpec(holding=[46608], models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Max Discharge Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 50)],
    )
    yield ModbusNumberDescription(
        key="max_discharge_current",
        address=[
            ModbusAddressSpec(input=41008, models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressSpec(
                holding=41008,
                models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.KH_PRE133 | Inv.KH_133 | Inv.H3_SET & ~Inv.AIO_H3_PRE101,
            ),
            ModbusAddressSpec(holding=46608, models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Max Discharge Current",
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=0,
        native_max_value=50,
        native_step=0.1,
        native_unit_of_measurement="A",
        scale=0.1,
        validate=[Range(0, 50)],
    )

    # Min SoC (Off Grid)
    yield ModbusSensorDescription(
        key="min_soc",
        addresses=[
            ModbusAddressesSpec(input=[8491], models=Inv.TREX),
            ModbusAddressesSpec(holding=[8491], models=Inv.TREX,),
        ],
        name="Battery Min SoC (Off Grid)",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
        native_unit_of_measurement="%",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="min_soc",
        address=[
            ModbusAddressSpec(input=8491, models=Inv.TREX),
            ModbusAddressSpec(holding=8491, models=Inv.TREX),
        ],
        name="Battery Min SoC (Off Grid)",
        mode=NumberMode.BOX,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        device_class=NumberDeviceClass.BATTERY,
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )

    # Max SoC
    yield ModbusSensorDescription(
        key="max_soc",
        addresses=[
            ModbusAddressesSpec(input=[41010], models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressesSpec(
                holding=[41010],
                models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101 | Inv.KH_PRE133 | Inv.KH_133,
            ),
            ModbusAddressesSpec(holding=[46610], models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Battery Max SoC",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        icon="mdi:battery-arrow-up",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="max_soc",
        address=[
            ModbusAddressSpec(input=41010, models=Inv.H1_G1 | Inv.KH_PRE119),
            ModbusAddressSpec(
                holding=41010,
                models=Inv.H1_G1 | Inv.H1_G2_SET | Inv.H3_SET & ~Inv.AIO_H3_PRE101 | Inv.KH_PRE133 | Inv.KH_133,
            ),
            ModbusAddressSpec(holding=46610, models=Inv.H3_PRO_SET | Inv.H3_SMART),
        ],
        name="Battery Max SoC",
        mode=NumberMode.BOX,
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="%",
        device_class=NumberDeviceClass.BATTERY,
        icon="mdi:battery-arrow-up",
        validate=[Range(0, 100)],
    )

    # Min SoC (On Grid)
    yield ModbusSensorDescription(
        key="min_soc_on_grid",
        addresses=[
            ModbusAddressesSpec(input=[8490], models=Inv.TREX),
            ModbusAddressesSpec(holding=[8490], models=Inv.TREX,),
        ],
        name="Battery Min SoC (On Grid)",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        icon="mdi:battery-arrow-down",
        validate=[Range(0, 100)],
    )
    yield ModbusNumberDescription(
        key="min_soc_on_grid",
        address=[
            ModbusAddressSpec(input=8490, models=Inv.TREX),
            ModbusAddressSpec(holding=8490, models=Inv.TREX),
        ],
        name="Battery Min SoC (On Grid)",
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
