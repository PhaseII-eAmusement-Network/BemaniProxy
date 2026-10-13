from pathlib import Path
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DBBase:
    engine: Engine = None
    SessionLocal = None

    @staticmethod
    def updateConfig(db_config: Dict[str, Any]) -> None:
        filepath = db_config.get('filepath', '')
        DATABASE_PATH = Path(filepath)
        DATABASE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection_string = f"sqlite:///{DATABASE_PATH.resolve()}"
        DBBase.engine = create_engine(
            connection_string,
            connect_args={
                "check_same_thread": False,
            },
        )
        DBBase.SessionLocal = sessionmaker(bind=DBBase.engine)

if DBBase.engine:
    Base.metadata.create_all(DBBase.engine)
