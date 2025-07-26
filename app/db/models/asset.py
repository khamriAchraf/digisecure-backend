from sqlalchemy import (CheckConstraint, Column, Date, DateTime, ForeignKey,
                        Integer, String)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.group import asset_groups


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    serial_number = Column(String, nullable=True)
    inventory_number = Column(String, nullable=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    status = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Security classification fields
    confidentiality_level = Column(String, nullable=True, default="Internal")
    integrity_level = Column(String, nullable=True, default="Medium")
    availability_level = Column(String, nullable=True, default="Medium")

    # Discriminator column for polymorphic inheritance
    type = Column(String(50), nullable=False)

    # Relationships
    manufacturer = relationship("Manufacturer")
    location = relationship("Location")
    groups = relationship("Group", secondary=asset_groups, back_populates="assets")
    assigned_user = relationship("User")

    # Polymorphic configuration
    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "asset"}

    # Database-level constraints for security classification fields
    __table_args__ = (
        CheckConstraint(
            confidentiality_level.in_(["Public", "Internal", "Confidential", "Secret"]),
            name="valid_confidentiality_level",
        ),
        CheckConstraint(
            integrity_level.in_(["High", "Medium", "Low"]), name="valid_integrity_level"
        ),
        CheckConstraint(
            availability_level.in_(["High", "Medium", "Low"]),
            name="valid_availability_level",
        ),
    )


class Computer(Asset):
    __tablename__ = "computers"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    cpu = Column(String, nullable=True)
    ram = Column(String, nullable=True)
    storage = Column(String, nullable=True)
    os = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    model = Column(String, nullable=True)
    hostname = Column(String, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "computer"}


class Printer(Asset):
    __tablename__ = "printers"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    model = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    connection_type = Column(String, nullable=True)  # USB, Network, Wireless
    print_technology = Column(String, nullable=True)  # Laser, Inkjet, Thermal
    max_resolution = Column(String, nullable=True)
    color_support = Column(String, nullable=True)  # Color, Monochrome
    duplex_support = Column(String, nullable=True)  # Yes, No

    __mapper_args__ = {"polymorphic_identity": "printer"}


class NetworkDevice(Asset):
    __tablename__ = "network_devices"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    device_type = Column(
        String, nullable=True
    )  # Switch, Router, Access Point, Firewall
    model = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    port_count = Column(Integer, nullable=True)
    connection_type = Column(String, nullable=True)  # Ethernet, WiFi, Fiber
    management_ip = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "network_device"}


class Phone(Asset):
    __tablename__ = "phones"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    model = Column(String, nullable=True)
    phone_type = Column(String, nullable=True)  # Desk Phone, Mobile, Soft Phone
    extension = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    phone_system = Column(String, nullable=True)  # VoIP System, PBX
    line_count = Column(Integer, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "phone"}


class Peripheral(Asset):
    __tablename__ = "peripherals"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    peripheral_type = Column(String, nullable=True)  # Keyboard, Mouse, Monitor, Headset
    model = Column(String, nullable=True)
    connection_type = Column(String, nullable=True)  # USB, Bluetooth, Wireless
    compatibility = Column(String, nullable=True)  # Windows, Mac, Linux
    special_features = Column(String, nullable=True)  # RGB, Wireless, Ergonomic

    __mapper_args__ = {"polymorphic_identity": "peripheral"}


class Consumable(Asset):
    __tablename__ = "consumables"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    consumable_type = Column(String, nullable=True)  # Toner, Paper, Ink, Batteries
    model = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    unit = Column(String, nullable=True)  # pieces, cartridges, reams
    expiry_date = Column(Date, nullable=True)
    compatible_with = Column(String, nullable=True)  # Compatible printer models

    __mapper_args__ = {"polymorphic_identity": "consumable"}


class Rack(Asset):
    __tablename__ = "racks"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    rack_type = Column(String, nullable=True)  # Server Rack, Network Rack, Storage Rack
    model = Column(String, nullable=True)
    height_units = Column(Integer, nullable=True)  # 42U, 24U, etc.
    width = Column(String, nullable=True)  # 19", 23", etc.
    depth = Column(String, nullable=True)
    max_weight_capacity = Column(String, nullable=True)
    location_details = Column(String, nullable=True)  # Data center, room, etc.

    __mapper_args__ = {"polymorphic_identity": "rack"}


class Cable(Asset):
    __tablename__ = "cables"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    cable_type = Column(String, nullable=True)  # Ethernet, Fiber, Power, HDMI
    model = Column(String, nullable=True)
    length = Column(String, nullable=True)
    connector_type = Column(String, nullable=True)  # RJ45, LC, SC, etc.
    category = Column(String, nullable=True)  # Cat5e, Cat6, Cat7, etc.
    color = Column(String, nullable=True)
    max_bandwidth = Column(String, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "cable"}


class SimCardItem(Asset):
    __tablename__ = "sim_card_items"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    sim_type = Column(String, nullable=True)  # Standard, Micro, Nano, eSIM
    iccid = Column(String, nullable=True)  # Integrated Circuit Card Identifier
    imsi = Column(String, nullable=True)  # International Mobile Subscriber Identity
    carrier = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    data_plan = Column(String, nullable=True)
    activation_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "sim_card_item"}


class VirtualMachine(Asset):
    __tablename__ = "virtual_machines"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)

    # Virtualization platform details
    hypervisor_type = Column(
        String, nullable=True
    )  # VMware, Hyper-V, KVM, Xen, VirtualBox
    hypervisor_version = Column(String, nullable=True)
    vm_platform = Column(String, nullable=True)  # vSphere, ESXi, Hyper-V Server, etc.

    # VM specifications
    cpu_cores = Column(Integer, nullable=True)
    memory_mb = Column(Integer, nullable=True)
    storage_gb = Column(Integer, nullable=True)
    os_type = Column(String, nullable=True)  # Windows, Linux, macOS
    os_version = Column(String, nullable=True)
    os_architecture = Column(String, nullable=True)  # x86_64, ARM64, etc.

    # Network configuration
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    network_segment = Column(String, nullable=True)  # DMZ, Internal, PCI, etc.
    vlan_id = Column(String, nullable=True)

    # Security and compliance fields
    pci_scope = Column(
        String, nullable=True, default="Out of Scope"
    )  # In Scope, Out of Scope
    cardholder_data_environment = Column(
        String, nullable=True
    )  # CDE, Connected-to, Out-of-Scope
    encryption_status = Column(
        String, nullable=True
    )  # Encrypted, Not Encrypted, Partial
    encryption_type = Column(String, nullable=True)  # AES-256, AES-128, etc.
    backup_encryption = Column(String, nullable=True)  # Yes, No, N/A

    # Access control and monitoring
    admin_access_restricted = Column(String, nullable=True)  # Yes, No
    multi_factor_auth_enabled = Column(String, nullable=True)  # Yes, No
    logging_enabled = Column(String, nullable=True)  # Yes, No
    monitoring_tool = Column(String, nullable=True)  # SIEM, IDS/IPS, etc.

    # Patch and vulnerability management
    last_patch_date = Column(Date, nullable=True)
    patch_level = Column(String, nullable=True)
    vulnerability_scan_date = Column(Date, nullable=True)
    vulnerability_status = Column(
        String, nullable=True
    )  # Compliant, Non-Compliant, Pending

    # Backup and disaster recovery
    backup_frequency = Column(String, nullable=True)  # Daily, Weekly, Monthly
    last_backup_date = Column(Date, nullable=True)
    backup_retention_days = Column(Integer, nullable=True)
    disaster_recovery_plan = Column(String, nullable=True)  # Yes, No, N/A

    # Virtualization security
    isolation_level = Column(String, nullable=True)  # High, Medium, Low
    resource_isolation = Column(String, nullable=True)  # Yes, No
    network_isolation = Column(String, nullable=True)  # Yes, No
    storage_isolation = Column(String, nullable=True)  # Yes, No

    # Compliance tracking
    pci_assessment_date = Column(Date, nullable=True)
    pci_compliance_status = Column(
        String, nullable=True
    )  # Compliant, Non-Compliant, In Progress
    next_assessment_date = Column(Date, nullable=True)
    compliance_notes = Column(String, nullable=True)

    # VM lifecycle
    power_state = Column(String, nullable=True)  # Running, Stopped, Suspended
    creation_date = Column(Date, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    scheduled_decommission_date = Column(Date, nullable=True)

    # Resource allocation
    cpu_allocation_percent = Column(Integer, nullable=True)
    memory_allocation_percent = Column(Integer, nullable=True)
    storage_allocation_percent = Column(Integer, nullable=True)

    # High availability and redundancy
    ha_enabled = Column(String, nullable=True)  # Yes, No
    redundancy_level = Column(String, nullable=True)  # None, N+1, N+2
    failover_capability = Column(String, nullable=True)  # Yes, No

    __mapper_args__ = {"polymorphic_identity": "virtual_machine"}
