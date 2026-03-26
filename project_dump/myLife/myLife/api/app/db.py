from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from .config import Config

connect_args = {'check_same_thread': False} if Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite') else {}
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, connect_args=connect_args, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))
Base = declarative_base()

def init_db(app):
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns():
    if engine.dialect.name != 'sqlite':
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if 'users' in tables:
        columns = {col['name'] for col in inspector.get_columns('users')}
        if 'coins' not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE users SET coins = 0 WHERE coins IS NULL"))
        if 'coin_rate' not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN coin_rate FLOAT DEFAULT 0.02"))
                conn.execute(text("UPDATE users SET coin_rate = 0.02 WHERE coin_rate IS NULL"))
    if 'quest_events' in tables:
        columns = {col['name'] for col in inspector.get_columns('quest_events')}
        if 'coins_earned' not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE quest_events ADD COLUMN coins_earned INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE quest_events SET coins_earned = 0 WHERE coins_earned IS NULL"))

# expose session factory
db_session = SessionLocal
