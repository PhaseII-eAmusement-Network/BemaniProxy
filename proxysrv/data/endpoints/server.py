
from proxysrv.data.database import DBBase
from proxysrv.data.models import RemoteServer

class RemoteServerData:
    @staticmethod
    def _serialize(data: RemoteServer) -> dict:
        return {
            "id": data.id,
            "name": data.name,
            "host": data.host,
            "port": data.port,
            "enabled": data.enabled,
            "description": data.description,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }

    @staticmethod
    def get_server(server_id: int) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(RemoteServer).filter(
                RemoteServer.id == server_id
            ).first()

            return (
                RemoteServerData._serialize(data)
                if data is not None else None
            )

    @staticmethod
    def search_server(name: str) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(RemoteServer).filter(
                RemoteServer.name == name
            ).first()

            return (
                RemoteServerData._serialize(data)
                if data is not None else None
            )

    @staticmethod
    def list_servers(
        enabled: bool | None = None,
    ) -> list[dict]:
        with DBBase.SessionLocal() as session:
            query = session.query(RemoteServer)

            if enabled is not None:
                query = query.filter(
                    RemoteServer.enabled == enabled
                )

            data = query.order_by(RemoteServer.name).all()

            return [
                RemoteServerData._serialize(item)
                for item in data
            ]

    @staticmethod
    def create_server(
        name: str,
        host: str,
        port: int,
        description: str | None = None,
        enabled: bool = True,
    ) -> dict:
        with DBBase.SessionLocal() as session:
            data = RemoteServer(
                name=name,
                host=host,
                port=port,
                description=description,
                enabled=enabled,
            )

            session.add(data)
            session.flush()

            result = RemoteServerData._serialize(data)
            session.commit()

            return result

    @staticmethod
    def set_enabled(
        server_id: int,
        enabled: bool,
    ) -> dict | None:
        with DBBase.SessionLocal() as session:
            data = session.query(RemoteServer).filter(
                RemoteServer.id == server_id
            ).first()

            if data is None:
                return None

            data.enabled = enabled
            session.flush()

            result = RemoteServerData._serialize(data)
            session.commit()

            return result

    @staticmethod
    def delete_server(server_id: int) -> bool:
        with DBBase.SessionLocal() as session:
            data = session.query(RemoteServer).filter(
                RemoteServer.id == server_id
            ).first()

            if data is None:
                return False

            session.delete(data)
            session.commit()

            return True
