"""
backend/db.py
=============
Inicialización de la base de datos SQLite vía SQLModel y utilidades de sesión.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from backend.config import DB_URL
from backend import models  # noqa: F401  (registra las tablas)

engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Crea las tablas si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Dependencia FastAPI: una sesión por request."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Sesión para uso fuera de FastAPI (scheduler, scripts)."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
