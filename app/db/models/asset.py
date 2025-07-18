from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


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
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Discriminator column for polymorphic inheritance
    type = Column(String(50), nullable=False)

    # Relationships
    manufacturer = relationship("Manufacturer")
    location = relationship("Location")
    group = relationship("Group")
    assigned_user = relationship("User")

    # Polymorphic configuration
    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "asset"}


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
