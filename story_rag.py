from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

import os
from utils.mongodb_client import mongo_client
from typing import List, Callable, Any
from collections import defaultdict 
from langchain_core.documents import Document
from data_model import LogEntry


DATABASE_NAME = os.getenv("MONGODB_DATA_DB")
COLLECTION_NAME = os.getenv("MONGODB_STORY_DATA_COLLECTION")
ROOT_PATH = os.path.dirname(__file__)
CHROMA_DB_DIR = 'chroma_data'

chroma_persist_path = os.path.join(ROOT_PATH, CHROMA_DB_DIR)


# Embed a single document as a test
vectorstore = Chroma(
    collection_name="rag-chroma",
    embedding_function=OpenAIEmbeddings(),
    persist_directory=chroma_persist_path
)

story_retriever = vectorstore.as_retriever()

def initialize_chroma_db() -> None:
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    cursor = collection.find({'addedToVectorDb': {'$ne': True}})
    texts: List[str] = []
    metadatas: List[str] = []
    ids = []
    metadata_fields = ['eventName', 'storyCode', 'avgTag', 'storyName', 'storyInfo', 'eventType', 'segmentIndex']
    for document in cursor:
        if 'content' not in document:
            continue
        texts.append(document['content'])
        metadatas.append({key: _if_none(value, '') for key, value in document.items() if key in metadata_fields})
        ids.append(document['_id'])
    cursor.close()

    length = len(texts)
    offset = 0
    batch_size = 100
    while offset < length:
        end = min(length, offset + batch_size)
        batch_texts = texts[offset:end]
        batch_metadatas = metadatas[offset:end]
        batch_ids = ids[offset:end]
        vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
        collection.update_many({'_id': {'$in': batch_ids}}, {'$set': {'addedToVectorDb': True}})
        print(f'Added segments from {offset} to {end - 1} to vector db')
        # Run this multiple times, avoid exceeding open ai limits.
        if offset > 1000:
            break
        offset += batch_size
    
         
def _doc_key(document: Document) -> str:
    metadata = document.metadata
    return metadata['eventName'] + metadata['storyCode'] + metadata['avgTag']

def _if_none(value: Any, default_value: Any) -> Any:
    return value if value != None else default_value

def _retrieve_and_rank(query: str, log_entry: LogEntry) -> str:
    log_entry.story_rag_query = query
    docs = story_retriever.get_relevant_documents(query)
    docs_by_kley = defaultdict(lambda: [])
    for doc in docs:
        key = _doc_key(doc)
        docs_by_kley[key].append(doc)
    result = ''
    for key, docs in docs_by_kley.items():
        docs.sort(key=lambda d: d.metadata['segmentIndex'])
        for i, doc in enumerate(docs):
            content = doc.page_content
            if i == 0:
                result += content
                continue
            content_start_index = content.find('segmentIndex')
            result += '\n' + content[content_start_index:]
        result += '\n'
    log_entry.story_rag_result = result
    return result

def create_story_retriver(log_entry: LogEntry) -> Callable[[str], str]:
    return lambda x: _retrieve_and_rank(x, log_entry)
    

if __name__ == '__main__':
    initialize_chroma_db()
    from utils import start_session
    print(_retrieve_and_rank('史尔特尔', start_session('test')))
