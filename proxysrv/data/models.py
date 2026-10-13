from __future__ import annotations
from typing import Any
from proxysrv.data.time import Time
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def current_time() -> Any:
    return Time.now()

class TimestampMixin:
    created_at: Mapped[Time] = mapped_column(
        DateTime,
        nullable=False,
        default=current_time,
    )

    updated_at: Mapped[Time] = mapped_column(
        DateTime,
        nullable=False,
        default=current_time,
        onupdate=current_time,
    )

class RemoteServer(TimestampMixin, Base):
    __tablename__ = "remote_servers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )
    # Hostname or IP address, IPv4 or IPv6.
    host: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    pcbid_assignments: Mapped[list[PCBIDRemoteServer]] = relationship(
        back_populates="remote_server",
    )
    __table_args__ = (
        CheckConstraint("port >= 1 AND port <= 65535", name="ck_remote_server_port"),
        Index("ix_remote_servers_enabled", "enabled"),
    )

class PCBID(TimestampMixin, Base):
    __tablename__ = "pcbids"
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    last_seen_at: Mapped[Time | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    collections: Mapped[list[PCBIDCollectionMember]] = relationship(
        back_populates="pcbid",
        cascade="all, delete-orphan",
    )
    remote_assignments: Mapped[list[PCBIDRemoteServer]] = relationship(
        back_populates="pcbid",
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        Index("ix_pcbids_verified", "verified"),
    )

class PCBIDCollection(TimestampMixin, Base):
    __tablename__ = "pcbid_collections"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    members: Mapped[list[PCBIDCollectionMember]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="PCBIDCollectionMember.id",
    )

class PCBIDCollectionMember(Base):
    __tablename__ = "pcbid_collection_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("pcbid_collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    pcbid_id: Mapped[int] = mapped_column(
        ForeignKey("pcbids.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_at: Mapped[Time] = mapped_column(
        DateTime,
        nullable=False,
        default=current_time,
    )
    collection: Mapped[PCBIDCollection] = relationship(
        back_populates="members",
    )
    pcbid: Mapped[PCBID] = relationship(
        back_populates="collections",
    )
    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "pcbid_id",
            name="uq_collection_pcbid",
        ),
        Index("ix_collection_members_pcbid", "pcbid_id"),
    )

class PCBIDRemoteServer(TimestampMixin, Base):
    """
    Tracks PCBID-to-server assignments.
    """
    __tablename__ = "pcbid_remote_servers"
    id: Mapped[int] = mapped_column(primary_key=True)
    pcbid_id: Mapped[int] = mapped_column(
        ForeignKey("pcbids.id", ondelete="CASCADE"),
        nullable=False,
    )
    remote_server_id: Mapped[int] = mapped_column(
        ForeignKey("remote_servers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    pcbid: Mapped[PCBID] = relationship(
        back_populates="remote_assignments",
    )
    remote_server: Mapped[RemoteServer] = relationship(
        back_populates="pcbid_assignments",
    )
    __table_args__ = (
        Index(
            "ix_pcbid_remote_active",
            "pcbid_id",
            "active",
        ),
        Index(
            "ix_remote_server_assignments",
            "remote_server_id",
            "active",
        ),
    )

class XMLRewriteRule(TimestampMixin, Base):
    """
    A rewrite ruleset.

    A NULL collection_id means the rule applies globally.
    A non-NULL collection_id scopes it to that PCBID collection.
    """
    __tablename__ = "xml_rewrite_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )
    collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("pcbid_collections.id", ondelete="CASCADE"),
        nullable=True,
    )
    collection: Mapped[PCBIDCollection | None] = relationship()
    nodes: Mapped[list[XMLRewriteNode]] = relationship(
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="XMLRewriteNode.position",
    )
    __table_args__ = (
        Index(
            "ix_xml_rewrite_scope",
            "enabled",
            "collection_id",
            "priority",
        ),
    )

class XMLRewriteNode(Base):
    """
    One node in a rewrite tree.

    `key` identifies the XML element/tag or attribute.
    `value` is the optional match value.
    `replacement_key` and `replacement_value` describe the rewrite.
    `operation` tells the rewrite engine what to do.
    """
    __tablename__ = "xml_rewrite_nodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("xml_rewrite_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("xml_rewrite_nodes.id", ondelete="CASCADE"),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    # XML key/tag being matched.
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    # Optional match condition; NULL means no value constraint.
    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # Examples: replace, rename, delete, insert.
    operation: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="replace",
    )
    replacement_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    replacement_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # Optional JSON-like metadata for future matching options.
    # Store serialized JSON here if you need additional conditions.
    options: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    rule: Mapped[XMLRewriteRule] = relationship(
        back_populates="nodes",
    )
    parent: Mapped[XMLRewriteNode | None] = relationship(
        back_populates="children",
        remote_side="XMLRewriteNode.id",
    )
    children: Mapped[list[XMLRewriteNode]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="XMLRewriteNode.position",
    )
    __table_args__ = (
        Index("ix_xml_rewrite_nodes_parent", "parent_id"),
        Index("ix_xml_rewrite_nodes_rule", "rule_id"),
    )
