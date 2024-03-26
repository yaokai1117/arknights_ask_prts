import os  # nopep8
import sys  # nopep8
ROOT_PATH = os.path.join(os.path.dirname(__file__), '..')  # nopep8
sys.path.append(ROOT_PATH)  # nopep8

import pymongo

MONGODB_URI = os.getenv("MONGODB_URI")

mongo_client = pymongo.MongoClient(MONGODB_URI, uuidRepresentation='standard')
