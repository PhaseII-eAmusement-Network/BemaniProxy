
from proxysrv.data.database import DBBase
from proxysrv.data.models import (
    PCBID,
    PCBIDCollection,
    PCBIDCollectionMember,
)

class PCBIDCollectionData:
    @staticmethod
    def _serialize(data: PCBIDCollection) -> dict:
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "enabled": data.enabled,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "members": [
                {
                    "id": member.pcbid.id,
                    "value": member.pcbid.value,
                    "verified": member.pcbid.verified,
                    "added_at": member.added_at,
                }
                for member in data.members
                if member.pcbid is not None
            ],
        }

    @staticmethod
    def get_collection(collection_id: int) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBIDCollection).filter(
                PCBIDCollection.id == collection_id
            ).first()

            if data is None:
                return None

            return PCBIDCollectionData._serialize(data)

    @staticmethod
    def search_collection(name: str) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBIDCollection).filter(
                PCBIDCollection.name == name
            ).first()

            if data is None:
                return None

            return PCBIDCollectionData._serialize(data)

    @staticmethod
    def list_collections(
        enabled: bool | None = None,
    ) -> list[dict]:
        with DBBase.SessionLocal() as session:
            query = session.query(PCBIDCollection)

            if enabled is not None:
                query = query.filter(
                    PCBIDCollection.enabled == enabled
                )

            data = query.order_by(PCBIDCollection.name).all()

            return [
                PCBIDCollectionData._serialize(item)
                for item in data
            ]

    @staticmethod
    def create_collection(
        name: str,
        description: str | None = None,
        enabled: bool = True,
    ) -> dict:
        with DBBase.SessionLocal() as session:
            data = PCBIDCollection(
                name=name,
                description=description,
                enabled=enabled,
            )

            session.add(data)
            session.flush()

            result = PCBIDCollectionData._serialize(data)
            session.commit()

            return result

    @staticmethod
    def add_pcbid(
        collection_id: int,
        inputPCBID: str,
    ) -> bool:
        with DBBase.SessionLocal() as session:
            collection = session.query(
                PCBIDCollection
            ).filter(
                PCBIDCollection.id == collection_id
            ).first()

            pcbid = session.query(PCBID).filter(
                PCBID.value == inputPCBID
            ).first()

            if collection is None or pcbid is None:
                return False

            existing = session.query(
                PCBIDCollectionMember
            ).filter(
                PCBIDCollectionMember.collection_id == collection_id,
                PCBIDCollectionMember.pcbid_id == pcbid.id,
            ).first()

            if existing is not None:
                return True

            session.add(
                PCBIDCollectionMember(
                    collection_id=collection.id,
                    pcbid_id=pcbid.id,
                )
            )
            session.commit()

            return True

    @staticmethod
    def remove_pcbid(
        collection_id: int,
        inputPCBID: str,
    ) -> bool:
        with DBBase.SessionLocal() as session:
            member = (
                session.query(PCBIDCollectionMember)
                .join(PCBIDCollectionMember.pcbid)
                .filter(
                    PCBIDCollectionMember.collection_id == collection_id,
                    PCBID.value == inputPCBID,
                )
                .first()
            )

            if member is None:
                return False

            session.delete(member)
            session.commit()

            return True

    @staticmethod
    def set_enabled(
        collection_id: int,
        enabled: bool,
    ) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBIDCollection).filter(
                PCBIDCollection.id == collection_id
            ).first()

            if data is None:
                return None

            data.enabled = enabled
            session.flush()

            result = PCBIDCollectionData._serialize(data)
            session.commit()

            return result

    @staticmethod
    def delete_collection(collection_id: int) -> bool:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBIDCollection).filter(
                PCBIDCollection.id == collection_id
            ).first()

            if data is None:
                return False

            session.delete(data)
            session.commit()

            return True
