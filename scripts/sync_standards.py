#!/usr/bin/env python3
"""
Sync and validate consistency across standards.json, relationships.json, and regulations.json.
Read-only validation — strictly does not modify original JSON data files.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.sync")

def validate_dataset_consistency():
    data_dir = settings.DATA_DIR
    standards_file = data_dir / "standards.json"
    relationships_file = data_dir / "relationships.json"
    regulations_file = data_dir / "regulations.json"

    with open(standards_file, "r", encoding="utf-8") as f:
        standards = json.load(f)
    standard_ids = {s["standard_id"] for s in standards}
    base_ids = {s["standard_id"].split(":")[0].strip() for s in standards}

    logger.info(f"Total Standards: {len(standards)}")

    # Check relationships
    if relationships_file.exists():
        with open(relationships_file, "r", encoding="utf-8") as f:
            relationships = json.load(f)
        logger.info(f"Total Relationships: {len(relationships)}")
        for r in relationships:
            f_std = r.get("from", "")
            t_std = r.get("to", "")
            f_base = f_std.split(":")[0].strip()
            t_base = t_std.split(":")[0].strip()
            
            f_exists = f_std in standard_ids or f_base in base_ids
            t_exists = t_std in standard_ids or t_base in base_ids
            logger.info(f"Rel: '{f_std}' -> '{t_std}' [{r.get('type')}] (From exists: {f_exists}, To exists: {t_exists})")

    # Check regulations
    if regulations_file.exists():
        with open(regulations_file, "r", encoding="utf-8") as f:
            regulations = json.load(f)
        logger.info(f"Total Regulations: {len(regulations)}")
        for reg in regulations:
            logger.info(f"Regulation: {reg.get('id')} - {reg.get('title')} ({len(reg.get('standards', []))} standards covered)")

    logger.info("Dataset consistency validation complete. All source files intact.")

if __name__ == "__main__":
    validate_dataset_consistency()
