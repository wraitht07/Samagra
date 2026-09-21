#!/usr/bin/env python3
"""
Ingest Indian Standards, Relationships, and Regulations into PostgreSQL / pgvector.
"""
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import SQLAlchemyError

from src.backend.ingestion import ingestion_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.ingest")

def main():
    logger.info("Starting Samagra standards ingestion...")
    counts = ingestion_manager.load_json_data()
    logger.info(f"Loaded JSON records: {counts}")
    
    try:
        ingestion_manager.sync_to_db()
        logger.info("Database synchronization completed successfully.")
    except (SQLAlchemyError, OSError) as e:
        logger.warning(f"Database sync encountered an issue: {e}. Dataset is available in in-memory index.")

    logger.info("Ingestion finished.")

if __name__ == "__main__":
    main()
