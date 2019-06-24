import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


class SqliteDB:
    def __init__(self, path, metadata, echo=False):
        self.path = path
        self.metadata = metadata
        self.echo = echo

        self._engine = None
        self._session_factory = None

    def unlink(self):
        try:
            if self._engine is not None:
                self._engine.dispose()

            self._engine = None
            self._session_factory = None

            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def _connect(self):
        engine = create_engine("sqlite:///{}".format(self.path), echo=self.echo)

        # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
        # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#foreign-key-support

        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            dbapi_connection.isolation_level = None
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        @event.listens_for(engine, "begin")
        def do_begin(conn):
            conn.execute("BEGIN")

        self.metadata.create_all(engine)

        return engine

    def _get_engine(self):
        if self._engine is None:
            self._engine = self._connect()
        return self._engine

    def _get_session_factory(self):
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self._get_engine(), expire_on_commit=False)
        return self._session_factory

    @contextmanager
    def session(self):
        session_factory = self._get_session_factory()
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
