import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()
GRAPHQL_PORT = os.getenv("GRAPHQL_PORT")
GRAPHQL_URL = f'http://127.0.0.1:{GRAPHQL_PORT}/'

class GraphQLCient():
    def query(self, query: str) -> dict:
        return json.loads(requests.post(url=GRAPHQL_URL, json={'query': query}).content)

graphql_client = GraphQLCient()
