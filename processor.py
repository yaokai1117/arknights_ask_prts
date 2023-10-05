from planner import Planner
from typing import List
from data_model import ToolType
from utils import graphql_client

class Processor():
    def __init__(self) -> None:
        self.planner = Planner()

    def process(self, question: str) -> List[dict]:
        planner_output = self.planner.process(question)
        print(planner_output)
        if not planner_output.succeeded:
            return [{'error': planner_output.error}]
        
        output: List[dict] = []
        if planner_output.tool_type == ToolType.game_data_graph_ql:
            for query in planner_output.tool_input:
                try:
                    query_result = graphql_client.query(query)
                except Exception as e:
                    return [{'error': f'Exception when calling graphql: {e}'}]
                output.append(query_result)
        elif planner_output.tool_type == ToolType.bilibili_search:
            # TODO: implemnt bilibili search tool.
            output.extend(planner_output.tool_input)
        return output
