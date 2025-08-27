from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from app.schemas.compliance_scope import ComplianceScopeForAsset


class Asset(BaseModel):
    id: int
    name: str
    type: str
    created_at: datetime
    updated_at: datetime


class DeletedAssetList(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    deleted_at: datetime
    created_at: datetime


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
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    location_id: Optional[int] = None
    group_ids: Optional[List[int]] = None
    assigned_to: Optional[int] = None

    confidentiality_level: Optional[str] = None
    integrity_level: Optional[str] = None
    availability_level: Optional[str] = None


class AssetInDBBase(AssetBase):
    id: int
    type: str
    created_at: datetime
    updated_at: datetime
    manufacturer: Optional[ManufacturerRef] = None
    location: Optional[LocationRef] = None
    groups: List[GroupRef] = []
    assigned_user: Optional[UserRef] = None
    compliance_scopes: List[ComplianceScopeForAsset] = []

    class Config:
        from_attributes = True


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


class ComputerList(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


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
    confidentiality_level: Optional[str] = None
    integrity_level: Optional[str] = None
    availability_level: Optional[str] = None


class Computer(AssetInDBBase, ComputerBase):
    type: Literal["computer"] = "computer"


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

    # Physical security
    rack_location: Optional[str] = None
    physical_lock: Optional[str] = None
    tamper_evident: Optional[str] = None

    # Network security
    vlan: Optional[str] = None
    segmentation: Optional[str] = None
    firewall_enabled: Optional[bool] = None
    ids_ips_enabled: Optional[bool] = None
    remote_access_enabled: Optional[bool] = None
    remote_access_method: Optional[str] = None
    remote_access_restriction: Optional[str] = None

    # Authentication and access control
    admin_username: Optional[str] = None
    admin_password_set: Optional[bool] = None
    password_last_changed: Optional[date] = None
    multi_factor_auth_enabled: Optional[bool] = None
    default_accounts_disabled: Optional[bool] = None

    # Logging and monitoring
    logging_enabled: Optional[bool] = None
    log_retention_days: Optional[int] = None
    syslog_server: Optional[str] = None
    snmp_enabled: Optional[bool] = None
    snmp_version: Optional[str] = None
    monitoring_tool: Optional[str] = None

    # Patch and vulnerability management
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    vulnerability_scan_date: Optional[date] = None
    vulnerability_status: Optional[str] = None

    # Encryption
    management_encryption: Optional[bool] = None
    encryption_type: Optional[str] = None
    data_in_transit_encryption: Optional[bool] = None

    # Device lifecycle
    power_state: Optional[str] = None
    creation_date: Optional[date] = None
    last_modified: Optional[datetime] = None
    scheduled_decommission_date: Optional[date] = None

    # Redundancy and high availability
    ha_enabled: Optional[bool] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[bool] = None


class NetworkDeviceCreate(NetworkDeviceBase):
    pass


class NetworkDeviceList(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


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

    # Physical security
    rack_location: Optional[str] = None
    physical_lock: Optional[str] = None
    tamper_evident: Optional[str] = None

    # Network security
    vlan: Optional[str] = None
    segmentation: Optional[str] = None
    firewall_enabled: Optional[bool] = None
    ids_ips_enabled: Optional[bool] = None
    remote_access_enabled: Optional[bool] = None
    remote_access_method: Optional[str] = None
    remote_access_restriction: Optional[str] = None

    # Authentication and access control
    admin_username: Optional[str] = None
    admin_password_set: Optional[bool] = None
    password_last_changed: Optional[date] = None
    multi_factor_auth_enabled: Optional[bool] = None
    default_accounts_disabled: Optional[bool] = None

    # Logging and monitoring
    logging_enabled: Optional[bool] = None
    log_retention_days: Optional[int] = None
    syslog_server: Optional[str] = None
    snmp_enabled: Optional[bool] = None
    snmp_version: Optional[str] = None
    monitoring_tool: Optional[str] = None

    # Patch and vulnerability management
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    vulnerability_scan_date: Optional[date] = None
    vulnerability_status: Optional[str] = None

    # Encryption
    management_encryption: Optional[bool] = None
    encryption_type: Optional[str] = None
    data_in_transit_encryption: Optional[bool] = None

    confidentiality_level: Optional[str] = None
    integrity_level: Optional[str] = None
    availability_level: Optional[str] = None

    # Device lifecycle
    power_state: Optional[str] = None
    creation_date: Optional[date] = None
    last_modified: Optional[datetime] = None
    scheduled_decommission_date: Optional[date] = None

    # Redundancy and high availability
    ha_enabled: Optional[bool] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[bool] = None


class NetworkDevice(AssetInDBBase, NetworkDeviceBase):
    type: Literal["network_device"] = "network_device"


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
    encryption_status: Optional[str] = None
    encryption_type: Optional[str] = None
    backup_encryption: Optional[bool] = None

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
    ha_enabled: Optional[bool] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[bool] = None


class VirtualMachineCreate(VirtualMachineBase):
    pass


class VirtualMachineList(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


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
    encryption_status: Optional[str] = None
    encryption_type: Optional[str] = None
    backup_encryption: Optional[bool] = None

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

    confidentiality_level: Optional[str] = None
    integrity_level: Optional[str] = None
    availability_level: Optional[str] = None

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
    ha_enabled: Optional[bool] = None
    redundancy_level: Optional[str] = None
    failover_capability: Optional[bool] = None


class VirtualMachine(AssetInDBBase, VirtualMachineBase):
    type: Literal["virtual_machine"] = "virtual_machine"

    class Config:
        from_attributes = True


# Software schemas
class SoftwareBase(AssetBase):
    vendor: Optional[str] = None
    description: Optional[str] = None
    software_type: Optional[str] = None

    # Encryption and security
    encryption_enabled: Optional[bool] = None
    encryption_type: Optional[str] = None
    encryption_key_management: Optional[str] = None
    secure_communication: Optional[bool] = None
    communication_protocol: Optional[str] = None

    # Authentication and access control
    authentication_required: Optional[bool] = None
    multi_factor_auth_supported: Optional[bool] = None
    role_based_access_control: Optional[bool] = None
    session_timeout_enabled: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None

    # Logging and monitoring
    audit_logging_enabled: Optional[bool] = None
    log_retention_days: Optional[int] = None
    log_integrity_protection: Optional[bool] = None
    centralized_logging: Optional[bool] = None

    # Vulnerability and patch management
    last_vulnerability_scan: Optional[date] = None
    vulnerability_status: Optional[str] = None
    known_vulnerabilities: Optional[str] = None
    patch_management_enabled: Optional[bool] = None
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    auto_update_enabled: Optional[bool] = None

    # Network security
    network_access_required: Optional[bool] = None
    firewall_rules_required: Optional[str] = None
    vpn_required: Optional[bool] = None
    network_segmentation: Optional[str] = None

    # Data protection and privacy
    data_retention_policy: Optional[str] = None
    data_backup_enabled: Optional[bool] = None
    data_encryption_at_rest: Optional[bool] = None

    # Software lifecycle
    end_of_life_date: Optional[date] = None
    end_of_support_date: Optional[date] = None
    replacement_planned: Optional[bool] = None
    replacement_software_id: Optional[int] = None

    # Performance and resource usage
    minimum_requirements: Optional[str] = None
    recommended_requirements: Optional[str] = None
    resource_usage_monitoring: Optional[bool] = None


class SoftwareCreate(SoftwareBase):
    pass


class SoftwareList(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SoftwareUpdate(BaseModel):
    # Base asset fields
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

    # Software specific
    vendor: Optional[str] = None
    description: Optional[str] = None
    software_type: Optional[str] = None

    encryption_enabled: Optional[bool] = None
    encryption_type: Optional[str] = None
    encryption_key_management: Optional[str] = None
    secure_communication: Optional[bool] = None
    communication_protocol: Optional[str] = None
    authentication_required: Optional[bool] = None
    multi_factor_auth_supported: Optional[bool] = None
    role_based_access_control: Optional[bool] = None
    session_timeout_enabled: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    audit_logging_enabled: Optional[bool] = None
    log_retention_days: Optional[int] = None
    log_integrity_protection: Optional[bool] = None
    centralized_logging: Optional[bool] = None
    last_vulnerability_scan: Optional[date] = None
    vulnerability_status: Optional[str] = None
    known_vulnerabilities: Optional[str] = None
    patch_management_enabled: Optional[bool] = None
    last_patch_date: Optional[date] = None
    patch_level: Optional[str] = None
    auto_update_enabled: Optional[bool] = None
    network_access_required: Optional[bool] = None
    firewall_rules_required: Optional[str] = None
    vpn_required: Optional[bool] = None
    network_segmentation: Optional[str] = None
    data_retention_policy: Optional[str] = None
    data_backup_enabled: Optional[bool] = None
    data_encryption_at_rest: Optional[bool] = None
    end_of_life_date: Optional[date] = None
    end_of_support_date: Optional[date] = None
    replacement_planned: Optional[bool] = None
    replacement_software_id: Optional[int] = None
    minimum_requirements: Optional[str] = None
    recommended_requirements: Optional[str] = None
    resource_usage_monitoring: Optional[bool] = None
    confidentiality_level: Optional[str] = None
    integrity_level: Optional[str] = None
    availability_level: Optional[str] = None


class Software(AssetInDBBase, SoftwareBase):
    type: Literal["software"] = "software"


# Software Version schemas
class SoftwareVersionBase(BaseModel):
    software_id: int
    version: str
    build_number: Optional[str] = None
    release_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    end_of_support_date: Optional[date] = None


class SoftwareVersionCreate(SoftwareVersionBase):
    pass


class SoftwareVersionUpdate(BaseModel):
    version: Optional[str] = None
    build_number: Optional[str] = None
    release_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    end_of_support_date: Optional[date] = None


class SoftwareVersion(SoftwareVersionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    software: Software

    class Config:
        from_attributes = True


class SoftwareVersionList(BaseModel):
    id: int
    version: str
    created_at: datetime
    updated_at: datetime
    build_number: Optional[str] = None
    release_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    end_of_support_date: Optional[date] = None


# Update Software schema to include versions relationship
class SoftwareWithVersions(Software):
    versions: List[SoftwareVersion] = []

    class Config:
        from_attributes = True


class CertificateKeyBase(AssetBase):
    cert_type: Optional[str] = None
    algorithm: Optional[str] = None
    storage_location: Optional[str] = None

    expiration_date: Optional[date] = None
    last_rotation_date: Optional[date] = None
    next_rotation_due: Optional[date] = None

    cert_status: Optional[str] = None

    issuer: Optional[str] = None
    subject: Optional[str] = None


class CertificateKeyCreate(CertificateKeyBase):
    pass


class CertificateKeyUpdate(AssetBase):
    cert_type: Optional[str] = None
    algorithm: Optional[str] = None
    storage_location: Optional[str] = None

    expiration_date: Optional[date] = None
    last_rotation_date: Optional[date] = None
    next_rotation_due: Optional[date] = None

    cert_status: Optional[str] = None

    issuer: Optional[str] = None
    subject: Optional[str] = None


class CertificateKeyList(BaseModel):
    id: int
    name: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CertificateKey(AssetInDBBase, CertificateKeyBase):
    type: Literal["certificate_key"] = "certificate_key"
