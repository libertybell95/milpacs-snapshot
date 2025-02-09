import os
from pymongo import MongoClient
from datetime import datetime, timezone
import requests
import logging
import sys
import schedule
import time
import zlib
import json

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/personnel_data")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
db = client.get_default_database()
collection = db["daily_snapshots"]

rosters = [
    "ROSTER_TYPE_COMBAT",
    "ROSTER_TYPE_RESERVE",
    "ROSTER_TYPE_ELOA",
    "ROSTER_TYPE_WALL_OF_HONOR",
    "ROSTER_TYPE_ARLINGTON",
    "ROSTER_TYPE_PAST_MEMBERS"
]

def setupLogging():
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    logger.setLevel(log_level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)


def getRoster(rosterName: str) -> dict:
    if not AUTH_TOKEN:
        logging.error("Auth token is not set. Please set the AUTH_TOKEN environment variable.")
        return {}

    response = requests.get(f"https://api.7cav.us/api/v1/roster/{rosterName}", 
                            headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
    
    if response.status_code != 200:
        logging.error(f"Failed to fetch {rosterName}: {response.status_code}")
        logging.error(response.text)
        return {}
    
    data = response.json()
    return data["profiles"]

def getAllRosters() -> dict:
    combined_profiles = []

    for roster in rosters:
        data = getRoster(roster)
        if data == {}:
            return {}
        for key, profile in data.items():
            combined_profiles.append(profile)

    return combined_profiles

def saveSnapshot():
    today = datetime.now(timezone.utc).isoformat()
    profiles = getAllRosters()
    if profiles == {}:
        logging.error("Failed to fetch rosters. Exiting.")
        return

    chunk_size = 500  # Adjust the chunk size as needed
    for i in range(0, len(profiles), chunk_size):
        chunk = profiles[i:i + chunk_size]
        collection.replace_one(
            {"snapshot_date": today, "chunk_index": i // chunk_size},
            {"snapshot_date": today, "chunk_index": i // chunk_size, "profiles": chunk},
            upsert=True
        )
    logging.info("Snapshot saved successfully! Timestamp: %s", today)
    
if __name__ == "__main__":
    setupLogging()
    saveSnapshot()
    schedule.every().day.at("00:00").do(saveSnapshot)
    while True:
        schedule.run_pending()
        time.sleep(30)
