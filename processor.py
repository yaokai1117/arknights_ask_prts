import json
import os
import requests

from dotenv import load_dotenv
from planner import Planner
from typing import List

load_dotenv()
GRAPHQL_PORT = os.getenv("GRAPHQL_PORT")
GRAPHQL_URL = f'http://127.0.0.1:{GRAPHQL_PORT}/'

class Processor():
    def __init__(self) -> None:
        self.planner = Planner()

    def process(self, question: str) -> List[dict]:
        planner_response = self.planner.process(question)
        result_json_idx = planner_response.find(Planner.OUTPUT_INDICATOR)
        if result_json_idx == -1:
            return 'Error: no final output returned from Planner.'
        result_json = planner_response[result_json_idx + len(Planner.OUTPUT_INDICATOR):]
        print(result_json)
        result = json.loads(result_json)
        if result['result_type'] == 'unrelated':
            return 'Error: Not related.'
        if result['tool_name'] != 'game_data_graph_ql':
            return f'Error: Should use tool {result["tool_name"]}'
        graphql_responses: List[str] = []
        for query in result['tool_input']:
            data = json.loads(requests.post(url=GRAPHQL_URL, json={'query': query}).content)
            graphql_responses.append(data)
        return graphql_responses
