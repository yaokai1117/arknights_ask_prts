import pymongo
import os
ROOT_PATH = os.path.join(os.path.dirname(__file__), '..')

import sys
sys.path.append(ROOT_PATH)

from dotenv import load_dotenv
from uuid import UUID, uuid4
from data_model import LogEntry, SessionStatus

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME =  os.getenv("MONGODB_LOGGING_DB")
COLLECTION_NAME = os.getenv("MONGODB_RAWENTRY_COLLECTION")

client = pymongo.MongoClient(MONGODB_URI, uuidRepresentation='standard')
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


# Start a logging session.
def start_session(initial_message: str, session_id: UUID = None) -> LogEntry:
    if session_id == None:
        session_id = uuid4()
    return LogEntry(session_id=session_id, initial_message=initial_message, status=SessionStatus.in_progress)

# Save an session to data base.
def save_session(entry: LogEntry) -> None:
    collection.replace_one({'session_id': entry.session_id}, entry.model_dump(), True)

# Finish an session with status and save it to db. 
def finish_session(entry: LogEntry, status: SessionStatus = None, error: str = None, final_response: str = None):
    if status != None:
        entry.status = status
    if error != None:
        entry.error = error
    if final_response != None:
        entry.final_response = final_response
    save_session(entry)
