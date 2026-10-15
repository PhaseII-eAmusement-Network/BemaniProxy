
from proxysrv.data.database import DBBase
from proxysrv.data.models import (
    PCBID,
    PCBIDRemoteServer,
)

class PCBIDData:
    @staticmethod
    def _serialize(data: PCBID) -> dict:
        return {
            "id": data.id,
            "value": data.value,
            "verified": data.verified,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "last_seen_at": data.last_seen_at,
            "collections": [
                {
                    "id": member.collection.id,
                    "name": member.collection.name,
                    "enabled": member.collection.enabled,
                    "added_at": member.added_at,
                }
                for member in data.collections
                if member.collection is not None
            ],
            "remote_assignments": [
                {
                    "id": assignment.id,
                    "active": assignment.active,
                    "remote_server": {
                        "id": assignment.remote_server.id,
                        "name": assignment.remote_server.name,
                        "host": assignment.remote_server.host,
                        "port": assignment.remote_server.port,
                        "enabled": assignment.remote_server.enabled,
                    },
                }
                for assignment in data.remote_assignments
                if assignment.remote_server is not None
            ],
        }

    @staticmethod
    def search_pcbid(inputPCBID: str) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = (
                session.query(PCBID)
                .filter(PCBID.value == inputPCBID)
                .first()
            )

            if data is None:
                return None
            return PCBIDData._serialize(data)

    @staticmethod
    def get_pcbid(pcbid_id: int) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBID).filter(
                PCBID.id == pcbid_id
            ).first()

            if data is None:
                return None
            return PCBIDData._serialize(data)

    @staticmethod
    def list_pcbids(
        verified: bool | None = None
    ) -> list[dict]:
        with DBBase.SessionLocal() as session:
            query = session.query(PCBID)
            if verified is not None:
                query = query.filter(PCBID.verified == verified)

            data = (query.order_by(PCBID.id).all())
            return [PCBIDData._serialize(item) for item in data]

    @staticmethod
    def create_pcbid(
        value: str,
        verified: bool = False,
    ) -> dict:
        with DBBase.SessionLocal() as session:
            data = PCBID(
                value=value,
                verified=verified,
            )

            session.add(data)
            session.flush()

            result = PCBIDData._serialize(data)
            session.commit()
            return result

    @staticmethod
    def set_verified(
        inputPCBID: str,
        verified: bool,
    ) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBID).filter(
                PCBID.value == inputPCBID
            ).first()

            if data is None:
                return None

            data.verified = verified
            session.flush()

            result = PCBIDData._serialize(data)
            session.commit()
            return result

    @staticmethod
    def update_last_seen(inputPCBID: str) -> bool:
        from proxysrv.data.time import Time

        with DBBase.SessionLocal() as session:
            data = session.query(PCBID).filter(
                PCBID.value == inputPCBID
            ).first()

            if data is None:
                return False

            data.last_seen_at = Time.now()
            session.commit()
            return True

    @staticmethod
    def delete_pcbid(inputPCBID: str) -> bool:
        with DBBase.SessionLocal() as session:
            data = session.query(PCBID).filter(
                PCBID.value == inputPCBID
            ).first()

            if data is None:
                return False

            session.delete(data)
            session.commit()
            return True

    @staticmethod
    def get_active_remote_server(
        inputPCBID: str,
    ) -> dict | None:
        with DBBase.SessionLocal() as session:
            assignment = (
                session.query(PCBIDRemoteServer)
                .join(PCBIDRemoteServer.pcbid)
                .join(PCBIDRemoteServer.remote_server)
                .filter(
                    PCBID.value == inputPCBID,
                    PCBIDRemoteServer.active.is_(True),
                    PCBIDRemoteServer.remote_server.has(
                        enabled=True
                    ),
                )
                .order_by(PCBIDRemoteServer.id)
                .first()
            )

            if assignment is None:
                return None
            
            server = assignment.remote_server
            return {
                "id": server.id,
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "enabled": server.enabled,
                "description": server.description,
            }
