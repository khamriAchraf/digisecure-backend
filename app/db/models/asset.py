import enum

from sqlalchemy import (Boolean, CheckConstraint, Column, Date, DateTime, Enum,
                        ForeignKey, Integer, String, Table)
from sqlalchemy.orm import Session, relationship

from app.db.base import Base, SoftDeleteMixin
from app.db.models.compliance_scopes import AssetComplianceScope
from app.db.models.document_store import software_docs
from app.db.models.group import asset_groups

software_version_computers = Table(
    "software_version_computers",
    Base.metadata,
    Column(
        "software_version_id",
        Integer,
        ForeignKey("software_versions.id"),
        primary_key=True,
    ),
    Column("computer_id", Integer, ForeignKey("computers.id"), primary_key=True),
)

software_version_virtual_machines = Table(
    "software_version_virtual_machines",
    Base.metadata,
    Column(
        "software_version_id",
        Integer,
        ForeignKey("software_versions.id"),
        primary_key=True,
    ),
    Column(
        "virtual_machine_id",
        Integer,
        ForeignKey("virtual_machines.id"),
        primary_key=True,
    ),
)

software_version_network_devices = Table(
    "software_version_network_devices",
    Base.metadata,
    Column(
        "software_version_id",
        Integer,
        ForeignKey("software_versions.id"),
        primary_key=True,
    ),
    Column(
        "network_device_id", Integer, ForeignKey("network_devices.id"), primary_key=True
    ),
)


class Asset(Base, SoftDeleteMixin):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    serial_number = Column(String, nullable=True)
    inventory_number = Column(String, nullable=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    status = Column(String, nullable=True)
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

    type = Column(String(50), nullable=False)

    # Relationships
    manufacturer = relationship("Manufacturer")
    location = relationship("Location")
    groups = relationship("Group", secondary=asset_groups, back_populates="assets")
    assigned_user = relationship("User")

    @property
    def compliance_scopes(self):
        scopes = []
        for mapping in self.compliance_mappings:
            scope_obj = mapping.scope

            # Attach mapping-specific attributes directly on the scope instance so that
            # Pydantic's `from_orm` picks them up when serialising using
            # `ComplianceScopeForAsset`.
            scope_obj.compliant = mapping.compliant
            scope_obj.justification = mapping.justification
            scope_obj.last_review_date = mapping.last_review_date
            scope_obj.next_review_date = mapping.next_review_date
            scope_obj.compliance_notes = mapping.compliance_notes

            scopes.append(scope_obj)

        return scopes

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "asset"}

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

    def soft_delete(self, db: Session):
        super().soft_delete()
        db.query(AssetComplianceScope).filter(
            AssetComplianceScope.asset_id == self.id
        ).delete()
        db.query(asset_groups).filter(asset_groups.c.asset_id == self.id).delete()
        db.query(software_version_computers).filter(
            software_version_computers.c.computer_id == self.id
        ).delete()
        db.query(software_version_computers).filter(
            software_version_computers.c.software_version_id == self.id
        ).delete()
        db.query(software_version_virtual_machines).filter(
            software_version_virtual_machines.c.virtual_machine_id == self.id
        ).delete()
        db.query(software_version_virtual_machines).filter(
            software_version_virtual_machines.c.software_version_id == self.id
        ).delete()
        db.query(software_version_network_devices).filter(
            software_version_network_devices.c.network_device_id == self.id
        ).delete()
        db.query(software_version_network_devices).filter(
            software_version_network_devices.c.software_version_id == self.id
        ).delete()
        return None


class Computer(Asset):
    __tablename__ = "computers"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    cpu = Column(String, nullable=True)
    ram = Column(String, nullable=True)
    storage = Column(String, nullable=True)
    operating_system_id = Column(
        Integer, ForeignKey("operating_systems.id"), nullable=True
    )
    mac_address = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    model = Column(String, nullable=True)
    hostname = Column(String, nullable=True)

    # Relationships
    operating_system = relationship("OperatingSystem")
    software_versions = relationship(
        "SoftwareVersion",
        secondary=software_version_computers,
        back_populates="computers",
    )

    __mapper_args__ = {"polymorphic_identity": "computer"}


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
    operating_system_id = Column(
        Integer, ForeignKey("operating_systems.id"), nullable=True
    )

    # Physical security
    rack_location = Column(String, nullable=True)
    physical_lock = Column(String, nullable=True)  # Yes, No
    tamper_evident = Column(String, nullable=True)  # Yes, No

    # Network security
    vlan = Column(String, nullable=True)
    segmentation = Column(String, nullable=True)  # PCI, Guest, Internal, etc.
    firewall_enabled = Column(Boolean, nullable=True)  # Yes, No
    ids_ips_enabled = Column(Boolean, nullable=True)  # Yes, No
    remote_access_enabled = Column(Boolean, nullable=True)  # Yes, No
    remote_access_method = Column(String, nullable=True)  # SSH, Telnet, HTTPS, etc.
    remote_access_restriction = Column(
        String, nullable=True
    )  # IP allowlist, VPN only, etc.

    # Authentication and access control
    admin_username = Column(String, nullable=True)
    admin_password_set = Column(Boolean, nullable=True)
    password_last_changed = Column(Date, nullable=True)
    multi_factor_auth_enabled = Column(Boolean, nullable=True)
    default_accounts_disabled = Column(Boolean, nullable=True)

    # Logging and monitoring
    logging_enabled = Column(Boolean, nullable=True)
    log_retention_days = Column(Integer, nullable=True)
    syslog_server = Column(String, nullable=True)
    snmp_enabled = Column(Boolean, nullable=True)
    snmp_version = Column(String, nullable=True)
    monitoring_tool = Column(String, nullable=True)  # SIEM, IDS/IPS, etc.

    # Patch and vulnerability management
    last_patch_date = Column(Date, nullable=True)
    patch_level = Column(String, nullable=True)
    vulnerability_scan_date = Column(Date, nullable=True)
    vulnerability_status = Column(
        String, nullable=True
    )  # Compliant, Non-Compliant, Pending

    # Encryption
    management_encryption = Column(Boolean, nullable=True)
    encryption_type = Column(String, nullable=True)  # AES-256, AES-128, etc.
    data_in_transit_encryption = Column(Boolean, nullable=True)

    # Device lifecycle
    power_state = Column(String, nullable=True)  # On, Off, Standby
    creation_date = Column(Date, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    scheduled_decommission_date = Column(Date, nullable=True)

    # Redundancy and high availability
    ha_enabled = Column(Boolean, nullable=True)
    redundancy_level = Column(String, nullable=True)  # None, N+1, N+2
    failover_capability = Column(Boolean, nullable=True)

    # Relationships
    software_versions = relationship(
        "SoftwareVersion",
        secondary=software_version_network_devices,
        back_populates="network_devices",
    )
    operating_system = relationship("OperatingSystem")

    __mapper_args__ = {"polymorphic_identity": "network_device"}


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
    operating_system_id = Column(
        Integer, ForeignKey("operating_systems.id"), nullable=True
    )

    # Network configuration
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    network_segment = Column(String, nullable=True)  # DMZ, Internal, PCI, etc.
    vlan_id = Column(String, nullable=True)

    # Security and compliance fields
    encryption_status = Column(
        String, nullable=True
    )  # Encrypted, Not Encrypted, Partial
    encryption_type = Column(String, nullable=True)  # AES-256, AES-128, etc.
    backup_encryption = Column(Boolean, nullable=True)

    # Access control and monitoring
    admin_access_restricted = Column(String, nullable=True)
    multi_factor_auth_enabled = Column(String, nullable=True)
    logging_enabled = Column(String, nullable=True)
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
    ha_enabled = Column(Boolean, nullable=True)
    redundancy_level = Column(String, nullable=True)  # None, N+1, N+2
    failover_capability = Column(Boolean, nullable=True)

    # Relationships
    operating_system = relationship("OperatingSystem")
    software_versions = relationship(
        "SoftwareVersion",
        secondary=software_version_virtual_machines,
        back_populates="virtual_machines",
    )

    __mapper_args__ = {"polymorphic_identity": "virtual_machine"}


class Software(Asset):
    __tablename__ = "software"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    vendor = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Software classification and type
    software_type = Column(
        String, nullable=True
    )  # Application, Operating System, Utility, Security Tool

    # Encryption and security
    encryption_enabled = Column(Boolean, nullable=True)
    encryption_type = Column(String, nullable=True)  # AES-256, AES-128, TLS 1.2, etc.
    encryption_key_management = Column(
        String, nullable=True
    )  # HSM, Software-based, Cloud KMS
    secure_communication = Column(Boolean, nullable=True)
    communication_protocol = Column(String, nullable=True)  # HTTPS, SFTP, SSH, etc.

    # Authentication and access control
    authentication_required = Column(Boolean, nullable=True)
    multi_factor_auth_supported = Column(Boolean, nullable=True)
    role_based_access_control = Column(Boolean, nullable=True)
    session_timeout_enabled = Column(Boolean, nullable=True)
    session_timeout_minutes = Column(Integer, nullable=True)

    # Logging and monitoring
    audit_logging_enabled = Column(Boolean, nullable=True)
    log_retention_days = Column(Integer, nullable=True)
    log_integrity_protection = Column(Boolean, nullable=True)
    centralized_logging = Column(Boolean, nullable=True)

    # Vulnerability and patch management
    last_vulnerability_scan = Column(Date, nullable=True)
    vulnerability_status = Column(
        String, nullable=True
    )  # Compliant, Non-Compliant, Pending
    known_vulnerabilities = Column(String, nullable=True)  # List of CVE IDs
    patch_management_enabled = Column(Boolean, nullable=True)
    last_patch_date = Column(Date, nullable=True)
    patch_level = Column(String, nullable=True)
    auto_update_enabled = Column(Boolean, nullable=True)

    # Network security
    network_access_required = Column(Boolean, nullable=True)
    firewall_rules_required = Column(String, nullable=True)  # Inbound, Outbound, Both
    vpn_required = Column(Boolean, nullable=True)
    network_segmentation = Column(String, nullable=True)  # PCI, Internal, DMZ, etc.

    data_retention_policy = Column(String, nullable=True)
    data_backup_enabled = Column(Boolean, nullable=True)
    data_encryption_at_rest = Column(Boolean, nullable=True)

    # Software lifecycle
    end_of_life_date = Column(Date, nullable=True)
    end_of_support_date = Column(Date, nullable=True)
    replacement_planned = Column(Boolean, nullable=True)
    replacement_software_id = Column(Integer, ForeignKey("software.id"), nullable=True)

    # Performance and resource usage
    minimum_requirements = Column(
        String, nullable=True
    )  # CPU, RAM, Storage requirements
    recommended_requirements = Column(String, nullable=True)
    resource_usage_monitoring = Column(Boolean, nullable=True)

    # Relationships
    replacement_software = relationship(
        "Software",
        remote_side=[id],
        foreign_keys=[replacement_software_id],
        uselist=False,
    )
    versions = relationship(
        "SoftwareVersion", back_populates="software", cascade="all, delete-orphan"
    )

    documents = relationship(
        "Document", secondary=software_docs, back_populates="software"
    )

    __table_args__ = (
        CheckConstraint(
            vulnerability_status.in_(["Compliant", "Non-Compliant", "Pending"]),
            name="valid_vulnerability_status",
        ),
    )

    __mapper_args__ = {"polymorphic_identity": "software"}


class SoftwareVersion(Base):
    __tablename__ = "software_versions"

    id = Column(Integer, primary_key=True, index=True)
    software_id = Column(Integer, ForeignKey("software.id"), nullable=False)
    version = Column(String, nullable=False)
    build_number = Column(String, nullable=True)
    release_date = Column(Date, nullable=True)
    end_of_life_date = Column(Date, nullable=True)
    end_of_support_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    software = relationship("Software", back_populates="versions")
    computers = relationship(
        "Computer",
        secondary=software_version_computers,
        back_populates="software_versions",
    )
    virtual_machines = relationship(
        "VirtualMachine",
        secondary=software_version_virtual_machines,
        back_populates="software_versions",
    )
    network_devices = relationship(  # pragma: allowlist secret
        "NetworkDevice",  # pragma: allowlist secret
        secondary=software_version_network_devices,
        back_populates="software_versions",
    )


class KeyType(enum.Enum):
    CERTIFICATE = "certificate"  # pragma: allowlist secret
    PRIVATE_KEY = "private_key"  # pragma: allowlist secret
    PUBLIC_KEY = "public_key"  # pragma: allowlist secret
    API_KEY = "api_key"  # pragma: allowlist secret
    SSH_KEY = "ssh_key"  # pragma: allowlist secret
    OTHER = "other"


class KeyStatus(enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    NEAR_EXPIRY = "near_expiry"
    EXPIRED = "expired"
    COMPROMISED = "compromised"


class CertificateKey(Asset):
    __tablename__ = "certificate_keys"

    id = Column(Integer, ForeignKey("assets.id"), primary_key=True)

    cert_type = Column(Enum(KeyType), nullable=False, default=KeyType.CERTIFICATE)
    algorithm = Column(String, nullable=True)
    storage_location = Column(String, nullable=True)

    expiration_date = Column(DateTime, nullable=True)
    last_rotation_date = Column(DateTime, nullable=True)
    next_rotation_due = Column(DateTime, nullable=True)

    cert_status = Column(Enum(KeyStatus), nullable=False, default=KeyStatus.ACTIVE)

    issuer = Column(String, nullable=True)
    subject = Column(String, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "certificate_key"}
