import os
import json
import requests


from .normalizer import normalize_graphql_query, denormalize_graphql_result
from typing import Dict, Any, Callable
from data_model import LogEntry, SessionStatus

GRAPHQL_PORT = os.getenv("GRAPHQL_PORT")
GRAPHQL_URL = f'http://127.0.0.1:{GRAPHQL_PORT}/'


class GraphQLCient():
    def query(self, query: str) -> dict:
        return json.loads(requests.post(url=GRAPHQL_URL, json={'query': query}).content)


graphql_client = GraphQLCient()


def _query_graphql(query: str, log_entry: LogEntry) -> str:
    try:
        query = normalize_graphql_query(query)
        log_entry.graphql_queries.append(query)
        query_result = graphql_client.query(query)
        denormalize_graphql_result(query_result)
        log_entry.graphql_results.append(query_result)
    except Exception as e:
        log_entry.status = SessionStatus.fail
        log_entry.error = f'GraphQL error: {e}'
        return ''

    return query_result


def create_graphql_callable(log_entry: LogEntry) -> Callable[[str], str]:
    return lambda x: _query_graphql(x, log_entry)
