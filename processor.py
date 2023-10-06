from planner import Planner
from typing import List
from data_model import PlannerOutputType, ToolType, SessionStatus
from utils import graphql_client, bilibili_search, start_session, finish_session
from utils import normalize_graphql_query, denormalize_graphql_result

class Processor():
    UNRELATED_RESPONSE = '这个问题似乎与明日方舟无关。'
    BILI_SEARCH_RESPONSE_HEADER = '在哔哩哔哩上搜索[{keywords}]的结果：\n{results}'

    def __init__(self) -> None:
        self.planner = Planner()

    async def process(self, question: str) -> List[dict]:
        log_entry = start_session(question)
        planner_output = self.planner.process(question, log_entry)
        log_entry.planner_output = planner_output
        if not planner_output.succeeded:
            finish_session(log_entry, status=SessionStatus.fail, error=f'Planner error: {planner_output.error}')
            return [{'error': planner_output.error}]
        
        if planner_output.type == PlannerOutputType.unrelated:
            finish_session(log_entry, status=SessionStatus.success, final_response=Processor.UNRELATED_RESPONSE)
            return [Processor.UNRELATED_RESPONSE]
        
        output: List[dict] = []
        if planner_output.tool_type == ToolType.game_data_graph_ql:
            for query in planner_output.tool_input:
                try:
                    query = normalize_graphql_query(query)
                    log_entry.graphql_queries.append(query)
                    query_result = graphql_client.query(query)
                    denormalize_graphql_result(query_result)
                except Exception as e:
                    finish_session(log_entry, status=SessionStatus.fail, error=f'GraphQL error: {e}')
                    return [{'error': f'Exception when calling graphql: {e}'}]
                output.append(query_result)
                log_entry.graphql_results.append(query_result)
        elif planner_output.tool_type == ToolType.bilibili_search:
            bili_result = await bilibili_search(planner_output.tool_input)
            output.append(self.BILI_SEARCH_RESPONSE_HEADER.format(keywords=planner_output.tool_input, results=bili_result))
        finish_session(log_entry, status=SessionStatus.success, final_response=output)
        return output
