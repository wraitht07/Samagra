import json
import logging
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, Column, Integer, String, Text, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from src.backend.config import settings

logger = logging.getLogger("samagra.ingestion")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

class StandardRecord(Base):
    __tablename__ = "standards"

    standard_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String, default="active")
    standard_type = Column(String, nullable=True)
    publication_year = Column(Integer, nullable=True)
    revision = Column(String, nullable=True)
    scope = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    certification = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    nasty_flag = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    verified = Column(Boolean, default=True)
    source = Column(String, nullable=True)
    supersedes = Column(JSON, nullable=True)
    superseded_by = Column(JSON, nullable=True)
    amendments = Column(JSON, nullable=True)

class RelationshipRecord(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_standard = Column(String, index=True)
    to_standard = Column(String, index=True)
    relationship_type = Column(String)
    note = Column(Text, nullable=True)

class RegulationRecord(Base):
    __tablename__ = "regulations"

    regulation_id = Column(String, primary_key=True)
    title = Column(String)
    ministry = Column(String)
    effective_from = Column(String)
    standards = Column(JSON)
    scheme = Column(String)
    notes = Column(Text)

class IngestionManager:
    """
    Manages loading and indexing the curated Indian Standards dataset.
    Maintains both Database (PostgreSQL/pgvector) and High-Speed In-Memory Indexes.
    """
    def __init__(self, data_dir: Optional[Path] = None, db_url: Optional[str] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.db_url = db_url or settings.DATABASE_URL
        
        self.standards_data: list[dict[str, Any]] = []
        self.standards_by_id: dict[str, dict[str, Any]] = {}
        self.relationships_data: list[dict[str, Any]] = []
        self.regulations_data: list[dict[str, Any]] = []
        
        self.engine = None
        self.Session = None
        self._init_db()

    def _init_db(self):
        try:
            self.engine = create_engine(self.db_url, pool_pre_ping=True)
            with self.engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                except SQLAlchemyError as e:
                    logger.warning(f"pgvector extension creation notice: {e}")
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection and tables initialized successfully.")
        except (SQLAlchemyError, OSError) as e:
            logger.warning(f"Could not connect to PostgreSQL ({e}). Using in-memory dataset mode.")
            self.engine = None
            self.Session = None

    def load_json_data(self) -> dict[str, int]:
        """Loads data directly from the read-only JSON source of truth."""
        standards_path = self.data_dir / "standards.json"
        relationships_path = self.data_dir / "relationships.json"
        regulations_path = self.data_dir / "regulations.json"

        if not standards_path.exists():
            raise FileNotFoundError(f"Missing standards dataset at {standards_path}")

        with open(standards_path, "r", encoding="utf-8") as f:
            self.standards_data = json.load(f)
            self.standards_by_id = {s["standard_id"]: s for s in self.standards_data}

        if relationships_path.exists():
            with open(relationships_path, "r", encoding="utf-8") as f:
                self.relationships_data = json.load(f)

        if regulations_path.exists():
            with open(regulations_path, "r", encoding="utf-8") as f:
                self.regulations_data = json.load(f)

        logger.info(
            f"Loaded {len(self.standards_data)} standards, "
            f"{len(self.relationships_data)} relationships, "
            f"{len(self.regulations_data)} regulations from JSON source."
        )
        return {
            "standards": len(self.standards_data),
            "relationships": len(self.relationships_data),
            "regulations": len(self.regulations_data),
        }

    def sync_to_db(self):
        """Populates PostgreSQL tables from the in-memory loaded JSON data."""
        if not self.Session:
            logger.warning("No database session available to sync.")
            return

        session = self.Session()
        try:
            # Sync standards
            for item in self.standards_data:
                rec = session.get(StandardRecord, item["standard_id"])
                if not rec:
                    rec = StandardRecord(standard_id=item["standard_id"])
                    session.add(rec)
                
                rec.title = item.get("title", "")
                rec.status = item.get("status", "active")
                rec.standard_type = item.get("standard_type")
                rec.publication_year = item.get("publication_year")
                rec.revision = item.get("revision")
                rec.scope = item.get("scope", "")
                rec.domain = item.get("domain")
                rec.certification = item.get("certification")
                rec.keywords = item.get("keywords", [])
                rec.nasty_flag = item.get("nasty_flag")
                rec.notes = item.get("notes")
                rec.verified = item.get("verified", True)
                rec.source = item.get("source")
                rec.supersedes = item.get("supersedes")
                rec.superseded_by = item.get("superseded_by")
                rec.amendments = item.get("amendments")

            # Sync relationships
            session.query(RelationshipRecord).delete()
            for r in self.relationships_data:
                session.add(
                    RelationshipRecord(
                        from_standard=r.get("from"),
                        to_standard=r.get("to"),
                        relationship_type=r.get("type"),
                        note=r.get("note"),
                    )
                )

            # Sync regulations
            for reg in self.regulations_data:
                reg_rec = session.get(RegulationRecord, reg["id"])
                if not reg_rec:
                    reg_rec = RegulationRecord(regulation_id=reg["id"])
                    session.add(reg_rec)
                reg_rec.title = reg.get("title")
                reg_rec.ministry = reg.get("ministry")
                reg_rec.effective_from = reg.get("effective_from")
                reg_rec.standards = reg.get("standards", [])
                reg_rec.scheme = reg.get("scheme")
                reg_rec.notes = reg.get("notes")

            session.commit()
            logger.info("Successfully synced standards to PostgreSQL.")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error syncing data to DB: {e}")
            raise
        finally:
            session.close()

    def get_standard(self, standard_id: str) -> Optional[dict[str, Any]]:
        return self.standards_by_id.get(standard_id)

    def get_all_standards(self) -> list[dict[str, Any]]:
        return self.standards_data

    def get_relationships_for(self, standard_id: str) -> list[dict[str, Any]]:
        rel_list = []
        base_id = standard_id.split(":")[0].strip()
        for r in self.relationships_data:
            r_from = r.get("from", "")
            r_to = r.get("to", "")
            if standard_id in (r_from, r_to) or base_id in (r_from.split(":")[0].strip(), r_to.split(":")[0].strip()):
                rel_list.append(r)
        return rel_list

    def get_regulations_for(self, standard_id: str) -> list[dict[str, Any]]:
        reg_list = []
        base_id = standard_id.split(":")[0].strip()
        for reg in self.regulations_data:
            stds = reg.get("standards", [])
            for s in stds:
                if s == standard_id or s.split(":")[0].strip() == base_id or standard_id.startswith(s):
                    reg_list.append(reg)
                    break
        return reg_list

ingestion_manager = IngestionManager()
ingestion_manager.load_json_data()
