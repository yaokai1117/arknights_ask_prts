import os  # nopep8

from .mongodb_client import mongo_client
from data_model import LogEntry, SessionStatus
from uuid import UUID, uuid4


DATABASE_NAME = os.getenv("MONGODB_LOGGING_DB")
COLLECTION_NAME = os.getenv("MONGODB_RAWENTRY_COLLECTION")

db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


# Start a logging session.
def start_session(initial_message: str, session_id: str = None) -> LogEntry:
    if session_id == None:
        session_id = uuid4()
    else:
        session_id = UUID(session_id)
    return LogEntry(session_id=session_id, initial_message=initial_message, status=SessionStatus.in_progress)

# Save an session to data base.


def save_session(entry: LogEntry) -> None:
    collection.replace_one({'session_id': entry.session_id}, entry.model_dump(), True)
