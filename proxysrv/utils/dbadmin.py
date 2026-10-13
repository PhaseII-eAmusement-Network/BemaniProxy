#!/usr/bin/env python3
"""Small interactive CRUD TUI for BemaniProxy's SQLAlchemy database.

Run from the repository root: python -m proxysrv.utils.dbadmin
Or place this file at proxysrv/utils/dbadmin.py and run the command above.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from proxysrv.data import models  # noqa: F401 - imports/registers all mappings
from proxysrv.data.database import Base

# Explicit model order keeps the most useful entities at the top of the menu.
MODEL_ORDER = (
    "PCBID", "PCBIDCollection", "RemoteServer", "PCBIDCollectionMember",
    "PCBIDRemoteServer", "XMLRewriteRule", "XMLRewriteNode",
)


def load_engine(config_path: Path, db_override: str | None = None):
    """Build an engine using the existing config.yaml database filepath."""
    if db_override:
        db_path = Path(db_override).expanduser().resolve()
    else:
        with config_path.open("r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream) or {}
        raw_path = (config.get("database") or {}).get("filepath", "./db/proxy.db")
        db_path = Path(raw_path).expanduser()
        if not db_path.is_absolute():
            db_path = (config_path.parent.parent / db_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, db_path


def model_classes() -> list[type]:
    by_name = {mapper.class_.__name__: mapper.class_ for mapper in Base.registry.mappers}
    names = [name for name in MODEL_ORDER if name in by_name]
    names.extend(sorted(name for name in by_name if name not in names))
    return [by_name[name] for name in names]


def label(model: type) -> str:
    return getattr(model, "__tablename__", model.__name__)


def columns(model: type):
    return list(inspect(model).columns)


def relationships(model: type):
    return list(inspect(model).relationships)


def display(value: Any, limit: int = 52) -> str:
    if value is None:
        result = "<null>"
    elif isinstance(value, bool):
        result = "yes" if value else "no"
    elif isinstance(value, datetime):
        result = value.isoformat(sep=" ", timespec="seconds")
    else:
        result = str(value).replace("\n", "\\n")
    return result if len(result) <= limit else result[: limit - 1] + "…"


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    if not rows:
        print("(no records)")
        return
    data = [[display(cell, 38) for cell in row] for row in rows]
    widths = [min(38, max(len(headers[i]), *(len(row[i]) for row in data))) for i in range(len(headers))]
    fmt = "  ".join("{:<" + str(width) + "}" for width in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["─" * width for width in widths]))
    for row in data:
        print(fmt.format(*[cell[:width] for cell, width in zip(row, widths)]))


def read_value(prompt: str, current: Any, column, session: Session) -> Any:
    """Prompt for one value and coerce it according to the mapped column."""
    python_type = column.type.python_type
    nullable = column.nullable
    while True:
        old = "" if current is None else str(current)
        suffix = f" [{old}]" if current is not None else (" [null]" if nullable else "")
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and current is not None:
            return current
        if raw == "" and nullable:
            return None
        if raw == "" and python_type is bool:
            return False
        try:
            if python_type is bool:
                lowered = raw.lower()
                if lowered in {"y", "yes", "true", "1", "on"}:
                    return True
                if lowered in {"n", "no", "false", "0", "off"}:
                    return False
                raise ValueError("enter yes/no")
            if python_type is int:
                return int(raw)
            if python_type is float:
                return float(raw)
            if python_type is datetime:
                value = datetime.fromisoformat(raw)
                return value
            if python_type is str:
                return raw
            return raw
        except (ValueError, TypeError) as exc:
            print(f"  Invalid value: {exc}")


def choose_foreign_key(session: Session, column) -> Any:
    """Offer existing target rows for a foreign-key column."""
    foreign_keys = list(column.foreign_keys)
    if not foreign_keys:
        return None
    fk = foreign_keys[0]
    target_table = fk.column.table.name
    target_model = next((m for m in model_classes() if m.__tablename__ == target_table), None)
    if target_model is None:
        return None
    target_pk = list(inspect(target_model).primary_key)[0]
    records = session.scalars(select(target_model).order_by(target_pk)).all()
    if not records:
        print(f"  No rows exist in {target_table}; create one first.")
        return None
    title_col = next((c for c in columns(target_model) if c.name in {"name", "value"}), target_pk)
    print_table(["ID", title_col.name], [[getattr(row, target_pk.key), getattr(row, title_col.key)] for row in records])
    while True:
        raw = input(f"  {column.name} (ID, blank for null): ").strip()
        if raw == "" and column.nullable:
            return None
        try:
            record = session.get(target_model, int(raw))
            if record is not None:
                return getattr(record, target_pk.key)
            print("  No matching ID.")
        except ValueError:
            print("  Enter a numeric ID.")


def edit_record(session: Session, model: type, record: Any | None = None) -> None:
    mapper = inspect(model)
    pk_columns = {column.key for column in mapper.primary_key}
    if record is None:
        record = model()
        is_new = True
    else:
        is_new = False

    for column in columns(model):
        if column.key in pk_columns or column.computed is not None or column.name in {"created_at", "updated_at", "added_at"}:
            continue
        current = getattr(record, column.key, None)
        if column.foreign_keys:
            value = choose_foreign_key(session, column)
            if value is None and not column.nullable:
                # For required foreign keys, let the user retry rather than save invalid data.
                while value is None:
                    print(f"  {column.name} is required.")
                    value = choose_foreign_key(session, column)
            setattr(record, column.key, value)
            continue
        default = column.default.arg if column.default is not None and not callable(column.default.arg) else None
        if current is None and default is not None:
            current = default
        setattr(record, column.key, read_value(column.name, current, column, session))

    # The project's current_time default returns an integer Unix timestamp,
    # while these columns are SQLAlchemy DateTime columns. Supply datetimes here
    # so admin-created records are valid without changing the proxy's public API.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if is_new and hasattr(record, "created_at"):
        record.created_at = now
    if hasattr(record, "updated_at"):
        record.updated_at = now
    if is_new and hasattr(record, "added_at"):
        record.added_at = now

    try:
        session.add(record)
        session.commit()
        print("Record created." if is_new else "Record updated.")
    except (IntegrityError, SQLAlchemyError) as exc:
        session.rollback()
        print(f"Save failed: {exc}")


def list_records(session: Session, model: type) -> list[Any]:
    mapper = inspect(model)
    pk = mapper.primary_key[0]
    records = session.scalars(select(model).order_by(pk).limit(200)).all()
    cols = columns(model)
    preferred = [c for c in cols if c.name in {"id", "name", "value", "host", "port", "enabled", "verified", "active", "priority", "collection_id", "rule_id", "pcbid_id", "remote_server_id", "key", "operation"}]
    if not preferred:
        preferred = cols[:5]
    print_table([c.name for c in preferred], [[getattr(row, c.key) for c in preferred] for row in records])
    if len(records) == 200:
        print("Showing first 200 records.")
    return records


def pick_record(session: Session, model: type):
    records = list_records(session, model)
    if not records:
        return None
    try:
        wanted = int(input("Record ID (blank to cancel): ").strip() or "0")
    except ValueError:
        print("Please enter a numeric ID.")
        return None
    if wanted == 0:
        return None
    record = session.get(model, wanted)
    if record is None:
        print("No record with that ID.")
    return record


def inspect_record(record: Any) -> None:
    print()
    for column in columns(type(record)):
        print(f"  {column.name:<24} {display(getattr(record, column.key), 100)}")
    for relationship in relationships(type(record)):
        if relationship.uselist:
            try:
                print(f"  {relationship.key + ' (related)':<24} {len(getattr(record, relationship.key))} record(s)")
            except Exception:
                pass
    print()


def delete_record(session: Session, model: type, record: Any) -> None:
    inspect_record(record)
    if input("Delete this record? Type DELETE to confirm: ") != "DELETE":
        print("Cancelled.")
        return
    try:
        session.delete(record)
        session.commit()
        print("Record deleted.")
    except (IntegrityError, SQLAlchemyError) as exc:
        session.rollback()
        print(f"Delete failed: {exc}")


def manage_model(session: Session, model: type) -> None:
    while True:
        print(f"\n{label(model)}")
        print("  1) List records\n  2) View record\n  3) Add record\n  4) Edit record\n  5) Delete record\n  0) Back")
        choice = input("> ").strip()
        if choice == "0":
            return
        if choice == "1":
            list_records(session, model)
        elif choice == "2":
            record = pick_record(session, model)
            if record is not None:
                inspect_record(record)
        elif choice == "3":
            edit_record(session, model)
        elif choice == "4":
            record = pick_record(session, model)
            if record is not None:
                edit_record(session, model, record)
        elif choice == "5":
            record = pick_record(session, model)
            if record is not None:
                delete_record(session, model, record)
        else:
            print("Choose one of the listed options.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive BemaniProxy database manager")
    parser.add_argument("--config", type=Path, default=Path("config/config.yaml"), help="path to config.yaml")
    parser.add_argument("--db", help="override SQLite database path")
    args = parser.parse_args()
    if not args.config.exists() and not args.db:
        parser.error(f"config file not found: {args.config}")

    try:
        engine, db_path = load_engine(args.config, args.db)
    except (OSError, yaml.YAMLError) as exc:
        print(f"Could not load database configuration: {exc}", file=sys.stderr)
        return 1

    print("BemaniProxy DB Manager")
    print(f"Database: {db_path}")
    print("Changes are committed immediately. Back up the SQLite file before bulk edits.\n")
    try:
        with Session(engine, expire_on_commit=False) as session:
            available_models = model_classes()
            while True:
                print("Tables")
                for index, model in enumerate(available_models, 1):
                    print(f"  {index:>2}) {label(model)}")
                print("   0) Exit")
                choice = input("> ").strip()
                if choice == "0":
                    break
                try:
                    model = available_models[int(choice) - 1]
                except (ValueError, IndexError):
                    print("Choose a valid table number.")
                    continue
                manage_model(session, model)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
