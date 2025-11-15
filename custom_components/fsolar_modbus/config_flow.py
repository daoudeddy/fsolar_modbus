"""Adds config flow for fsolar_modbus."""

import logging

from .const import DOMAIN
from .flow.flow_handler import FlowHandler

_LOGGER = logging.getLogger(__name__)


class ModbusFlowHandler(FlowHandler, domain=DOMAIN):
    pass
