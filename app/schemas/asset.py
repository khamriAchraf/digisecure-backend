from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class Asset(BaseModel):
    id: int
    name: str
    type: str
    created_at: datetime
    updated_at: datetime


# Simplified schemas for relationships
class ManufacturerRef(BaseModel):
    id: int
    name: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class LocationRef(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    town: Optional[str] = None
    country: Optional[str] = None

    class Config:
        from_attributes = True


class GroupRef(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    type: Optional[str] = None

    class Config:
        from_attributes = True


class UserRef(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class AssetBase(BaseModel):
    name: str
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: str
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None


class AssetInDBBase(AssetBase):
    id: int
    type: str
    created_at: datetime
    updated_at: datetime
    manufacturer: Optional[ManufacturerRef] = None
    location: Optional[LocationRef] = None
    groups: List[GroupRef] = []
    assigned_user: Optional[UserRef] = None

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


class ComputerUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class NetworkDeviceUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class PhoneUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class PeripheralUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class ConsumableUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class RackUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class CableUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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


class SimCardItemUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None
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

    class Config:
        from_attributes = True


# VirtualMachine schemas
class VirtualMachineBase(AssetBase):
    # Virtualization platform details
    hypervisor_type: Optional[str] = None
    hypervisor_version: Optional[str] = None
    vm_platform: Optional[str] = None

    # VM specifications
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    storage_gb: Optional[int] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    os_architecture: Optional[str] = None

    # Network configuration
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    network_segment: Optional[str] = None
    vlan_id: Optional[str] = None

    # Security and compliance fields
    pci_scope: Optional[str] = None
    cardholder_data_environment: Optional[str] = None
    encryption_status: Optional[str] = None
    encryption_type: Optional[str] = None
    backup_encryption: Optional[str] = None

    # Access control and monitoring
    admin_access_restricted: Optional[str] = None
    multi_factor_auth_enabled: Optional[str] = None
    logging_enabled: Optional[str] = None
    monitoring_tool: Optional[str] = None

    # Patch and vulnerability management
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    vulnerability_scan_date: Optional[date] = None
    vulnerability_status: Optional[str] = None

    # Backup and disaster recovery
    backup_frequency: Optional[str] = None
    last_backup_date: Optional[date] = None
    backup_retention_days: Optional[int] = None
    disaster_recovery_plan: Optional[str] = None

    # Virtualization security
    isolation_level: Optional[str] = None
    resource_isolation: Optional[str] = None
    network_isolation: Optional[str] = None
    storage_isolation: Optional[str] = None

    # Compliance tracking
    pci_assessment_date: Optional[date] = None
    pci_compliance_status: Optional[str] = None
    next_assessment_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    # VM lifecycle
    power_state: Optional[str] = None
    creation_date: Optional[date] = None
    last_modified: Optional[datetime] = None
    scheduled_decommission_date: Optional[date] = None

    # Resource allocation
    cpu_allocation_percent: Optional[int] = None
    memory_allocation_percent: Optional[int] = None
    storage_allocation_percent: Optional[int] = None

    # High availability and redundancy
    ha_enabled: Optional[str] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[str] = None


class VirtualMachineCreate(VirtualMachineBase):
    pass


class VirtualMachineUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None

    # Virtualization platform details
    hypervisor_type: Optional[str] = None
    hypervisor_version: Optional[str] = None
    vm_platform: Optional[str] = None

    # VM specifications
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    storage_gb: Optional[int] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    os_architecture: Optional[str] = None

    # Network configuration
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    network_segment: Optional[str] = None
    vlan_id: Optional[str] = None

    # Security and compliance fields
    pci_scope: Optional[str] = None
    cardholder_data_environment: Optional[str] = None
    encryption_status: Optional[str] = None
    encryption_type: Optional[str] = None
    backup_encryption: Optional[str] = None

    # Access control and monitoring
    admin_access_restricted: Optional[str] = None
    multi_factor_auth_enabled: Optional[str] = None
    logging_enabled: Optional[str] = None
    monitoring_tool: Optional[str] = None

    # Patch and vulnerability management
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    vulnerability_scan_date: Optional[date] = None
    vulnerability_status: Optional[str] = None

    # Backup and disaster recovery
    backup_frequency: Optional[str] = None
    last_backup_date: Optional[date] = None
    backup_retention_days: Optional[int] = None
    disaster_recovery_plan: Optional[str] = None

    # Virtualization security
    isolation_level: Optional[str] = None
    resource_isolation: Optional[str] = None
    network_isolation: Optional[str] = None
    storage_isolation: Optional[str] = None

    # Compliance tracking
    pci_assessment_date: Optional[date] = None
    pci_compliance_status: Optional[str] = None
    next_assessment_date: Optional[date] = None
    compliance_notes: Optional[str] = None

    # VM lifecycle
    power_state: Optional[str] = None
    creation_date: Optional[date] = None
    last_modified: Optional[datetime] = None
    scheduled_decommission_date: Optional[date] = None

    # Resource allocation
    cpu_allocation_percent: Optional[int] = None
    memory_allocation_percent: Optional[int] = None
    storage_allocation_percent: Optional[int] = None

    # High availability and redundancy
    ha_enabled: Optional[str] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[str] = None


class VirtualMachine(AssetInDBBase, VirtualMachineBase):
    type: Literal["virtual_machine"] = "virtual_machine"

    class Config:
        from_attributes = True
