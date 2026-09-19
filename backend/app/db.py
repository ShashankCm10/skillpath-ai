"""Small SQLite persistence layer used when SQLAlchemy is installed."""
from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///./skillpath.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase): pass
class AnalysisRecord(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    target_job: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)

def init_db() -> None:
    Base.metadata.create_all(engine)
