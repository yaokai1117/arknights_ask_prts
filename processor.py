from planner import Planner
from summarizer import Summarizer
from typing import List
from data_model import PlannerOutputType, ToolType, SessionStatus
from utils import graphql_client, bilibili_search, start_session, finish_session, save_session
from utils import normalize_graphql_query, denormalize_graphql_result

class Processor():
    NO_IDEA_RESPONSE = '不知道诶。。。'
    UNRELATED_RESPONSE = '这个问题似乎与明日方舟无关。'
    BILI_SEARCH_RESPONSE_HEADER = '在哔哩哔哩上搜索[{keywords}]的结果：\n{results}'

    def __init__(self) -> None:
        self.planner = Planner()
        self.summarizer = Summarizer()

    async def process(self, question: str) -> List[dict]:
        log_entry = start_session(question)
        planner_output = self.planner.process(question, log_entry)
        log_entry.planner_output = planner_output
        if not planner_output.succeeded:
            finish_session(log_entry, status=SessionStatus.fail, error=f'Planner error: {planner_output.error}', final_response=Processor.NO_IDEA_RESPONSE)
            return [Processor.NO_IDEA_RESPONSE]
        
        if planner_output.type == PlannerOutputType.unrelated:
            finish_session(log_entry, status=SessionStatus.success, final_response=Processor.UNRELATED_RESPONSE)
            return [Processor.UNRELATED_RESPONSE]
        
        final_reponse: str
        if planner_output.tool_type == ToolType.game_data_graph_ql:
            query_results: List[dict] = []
            for query in planner_output.tool_input:
                try:
                    query = normalize_graphql_query(query)
                    log_entry.graphql_queries.append(query)
                    query_result = graphql_client.query(query)
                    denormalize_graphql_result(query_result)
                except Exception as e:
                    log_entry.status = SessionStatus.fail
                    log_entry.error = f'GraphQL error: {e}'
                    continue
                query_results.append(query_result)
                log_entry.graphql_results.append(query_result)
            if log_entry.status != SessionStatus.fail:
                final_reponse = self.summarizer.process(question, planner_output.tool_input, query_results, log_entry)

            if log_entry.status == SessionStatus.fail:
                # Fallback to bilibili search when graphql failed.
                log_entry.fall_back_tool = ToolType.bilibili_search
                try:
                    search_result = await bilibili_search([question])
                    bili_result = self.BILI_SEARCH_RESPONSE_HEADER.format(keywords=question, results=search_result)
                except Exception as e:
                    bili_result = Processor.NO_IDEA_RESPONSE
                finally:
                    final_reponse = bili_result
                    log_entry.final_response = final_reponse
                    save_session(log_entry)
                    return final_reponse

        elif planner_output.tool_type == ToolType.bilibili_search:
            try:
                search_result = await bilibili_search(planner_output.tool_input)
                bili_result = self.BILI_SEARCH_RESPONSE_HEADER.format(keywords=planner_output.tool_input, results=search_result)
            except Exception as e:
                bili_result = Processor.NO_IDEA_RESPONSE
                final_reponse = bili_result
                finish_session(log_entry, status=SessionStatus.fail, error=f'Bilibili search error: {e}', final_response=final_reponse)
                return final_reponse
            final_reponse = bili_result
        finish_session(log_entry, status=SessionStatus.success, final_response=final_reponse)
        return final_reponse
