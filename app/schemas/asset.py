from datetime import date, datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel


class AssetBase(BaseModel):
    name: str
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: str
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_to: Optional[int] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_to: Optional[int] = None


class AssetInDBBase(AssetBase):
    id: int
    type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Computer schemas
class ComputerBase(AssetBase):
    cpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    os: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None
    hostname: Optional[str] = None


class ComputerCreate(ComputerBase):
    pass


class ComputerUpdate(AssetUpdate):
    cpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    os: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None
    hostname: Optional[str] = None


class Computer(AssetInDBBase, ComputerBase):
    type: Literal["computer"] = "computer"


# Printer schemas
class PrinterBase(AssetBase):
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    connection_type: Optional[str] = None
    print_technology: Optional[str] = None
    max_resolution: Optional[str] = None
    color_support: Optional[str] = None
    duplex_support: Optional[str] = None


class PrinterCreate(PrinterBase):
    pass


class PrinterUpdate(AssetUpdate):
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    connection_type: Optional[str] = None
    print_technology: Optional[str] = None
    max_resolution: Optional[str] = None
    color_support: Optional[str] = None
    duplex_support: Optional[str] = None


class Printer(AssetInDBBase, PrinterBase):
    type: Literal["printer"] = "printer"


# NetworkDevice schemas
class NetworkDeviceBase(AssetBase):
    device_type: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port_count: Optional[int] = None
    connection_type: Optional[str] = None
    management_ip: Optional[str] = None
    firmware_version: Optional[str] = None


class NetworkDeviceCreate(NetworkDeviceBase):
    pass


class NetworkDeviceUpdate(AssetUpdate):
    device_type: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port_count: Optional[int] = None
    connection_type: Optional[str] = None
    management_ip: Optional[str] = None
    firmware_version: Optional[str] = None


class NetworkDevice(AssetInDBBase, NetworkDeviceBase):
    type: Literal["network_device"] = "network_device"


# Phone schemas
class PhoneBase(AssetBase):
    model: Optional[str] = None
    phone_type: Optional[str] = None
    extension: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    phone_system: Optional[str] = None
    line_count: Optional[int] = None


class PhoneCreate(PhoneBase):
    pass


class PhoneUpdate(AssetUpdate):
    model: Optional[str] = None
    phone_type: Optional[str] = None
    extension: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    phone_system: Optional[str] = None
    line_count: Optional[int] = None


class Phone(AssetInDBBase, PhoneBase):
    type: Literal["phone"] = "phone"


# Peripheral schemas
class PeripheralBase(AssetBase):
    peripheral_type: Optional[str] = None
    model: Optional[str] = None
    connection_type: Optional[str] = None
    compatibility: Optional[str] = None
    special_features: Optional[str] = None


class PeripheralCreate(PeripheralBase):
    pass


class PeripheralUpdate(AssetUpdate):
    peripheral_type: Optional[str] = None
    model: Optional[str] = None
    connection_type: Optional[str] = None
    compatibility: Optional[str] = None
    special_features: Optional[str] = None


class Peripheral(AssetInDBBase, PeripheralBase):
    type: Literal["peripheral"] = "peripheral"


# Consumable schemas
class ConsumableBase(AssetBase):
    consumable_type: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    expiry_date: Optional[date] = None
    compatible_with: Optional[str] = None


class ConsumableCreate(ConsumableBase):
    pass


class ConsumableUpdate(AssetUpdate):
    consumable_type: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    expiry_date: Optional[date] = None
    compatible_with: Optional[str] = None


class Consumable(AssetInDBBase, ConsumableBase):
    type: Literal["consumable"] = "consumable"


# Rack schemas
class RackBase(AssetBase):
    rack_type: Optional[str] = None
    model: Optional[str] = None
    height_units: Optional[int] = None
    width: Optional[str] = None
    depth: Optional[str] = None
    max_weight_capacity: Optional[str] = None
    location_details: Optional[str] = None


class RackCreate(RackBase):
    pass


class RackUpdate(AssetUpdate):
    rack_type: Optional[str] = None
    model: Optional[str] = None
    height_units: Optional[int] = None
    width: Optional[str] = None
    depth: Optional[str] = None
    max_weight_capacity: Optional[str] = None
    location_details: Optional[str] = None


class Rack(AssetInDBBase, RackBase):
    type: Literal["rack"] = "rack"


# Cable schemas
class CableBase(AssetBase):
    cable_type: Optional[str] = None
    model: Optional[str] = None
    length: Optional[str] = None
    connector_type: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    max_bandwidth: Optional[str] = None


class CableCreate(CableBase):
    pass


class CableUpdate(AssetUpdate):
    cable_type: Optional[str] = None
    model: Optional[str] = None
    length: Optional[str] = None
    connector_type: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    max_bandwidth: Optional[str] = None


class Cable(AssetInDBBase, CableBase):
    type: Literal["cable"] = "cable"


# SimCardItem schemas
class SimCardItemBase(AssetBase):
    sim_type: Optional[str] = None
    iccid: Optional[str] = None
    imsi: Optional[str] = None
    carrier: Optional[str] = None
    phone_number: Optional[str] = None
    data_plan: Optional[str] = None
    activation_date: Optional[date] = None
    expiry_date: Optional[date] = None


class SimCardItemCreate(SimCardItemBase):
    pass


class SimCardItemUpdate(AssetUpdate):
    sim_type: Optional[str] = None
    iccid: Optional[str] = None
    imsi: Optional[str] = None
    carrier: Optional[str] = None
    phone_number: Optional[str] = None
    data_plan: Optional[str] = None
    activation_date: Optional[date] = None
    expiry_date: Optional[date] = None


class SimCardItem(AssetInDBBase, SimCardItemBase):
    type: Literal["sim_card_item"] = "sim_card_item"


# Union type for all asset types
AssetUnion = Union[
    Computer,
    Printer,
    NetworkDevice,
    Phone,
    Peripheral,
    Consumable,
    Rack,
    Cable,
    SimCardItem,
]


# Generic asset type (for backward compatibility)
class Asset(AssetInDBBase):
    pass


class AssetInDB(AssetInDBBase):
    pass
