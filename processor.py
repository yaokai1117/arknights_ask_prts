from planner import Planner
from summarizer import Summarizer
from typing import Dict, Any
from data_model import PlannerOutput, PlannerOutputType, ToolType, ToolInput, SessionStatus, LogEntry
from story_rag import create_story_retriver
from langchain_core.runnables import RunnableBranch

from utils import create_graphql_callable, bilibili_search

question_key = 'question'
planner_output_key = 'planner_output'


class Processor():
    NO_IDEA_RESPONSE = '不知道诶。。。'
    UNRELATED_RESPONSE = '这个问题似乎与明日方舟无关。'
    INPUT_KEY = Planner.input_key

    def __init__(self, log_entry: LogEntry) -> None:
        self.log_entry = log_entry
        
        self.planner = Planner(log_entry)
        self.summarizer = Summarizer(log_entry)
        self.graphql_callable = create_graphql_callable(self.log_entry)
        self.story_rag_retriver = create_story_retriver(self.log_entry)
        
        self.tool_caller = RunnableBranch(
            (lambda x: x.tool_type == ToolType.game_data_graph_ql, lambda x: ('game_data_graph_ql', x.tool_input, self.graphql_callable(x.tool_input))),
            (lambda x: x.tool_type == ToolType.story_database, lambda x: ('story_database', x.tool_input, self.story_rag_retriver(x.tool_input))),
            (lambda x: x.tool_type == ToolType.bilibili_search, lambda x: ('bilibili_search', x.tool_input, bilibili_search(x.tool_input))),
            lambda x: Processor.NO_IDEA_RESPONSE,
        )

        self.chain = (
            self.planner |
            (lambda x: {question_key: x[Planner.input_key],
                        planner_output_key: PlannerOutput.model_validate(x)}) |
            RunnableBranch(
                (lambda x: not x[planner_output_key].succeeded, self._handle_plan_failure),
                (lambda x: x[planner_output_key].type == PlannerOutputType.unrelated, self._handle_plan_unrelated),
                (lambda x: x[planner_output_key].type == PlannerOutputType.solvable_by_tool,
                 (self._call_tools | self.summarizer | (lambda x: x[Summarizer.output_key]))),
                lambda x: Processor.NO_IDEA_RESPONSE) |
            self._log_final_response)

    def _handle_plan_failure(self, x: Dict[str, Any]) -> str:
        planner_output = x[planner_output_key]
        self.log_entry.status = SessionStatus.fail
        self.log_entry.error = f'Planner error: {planner_output.error}'
        self.log_entry.final_response = Processor.NO_IDEA_RESPONSE
        return Processor.NO_IDEA_RESPONSE

    def _handle_plan_unrelated(self, x: Dict[str, Any]) -> str:
        self.log_entry.status = SessionStatus.success
        self.log_entry.final_response = Processor.UNRELATED_RESPONSE
        return Processor.UNRELATED_RESPONSE
    
    async def _call_tools(self, x: Dict[str, Any]) -> Dict[str, Any]:
        question = x[question_key]
        planner_output = x[planner_output_key]
        tool_context = await self.tool_caller.abatch(planner_output.inputs)
        return {Summarizer.question_key: question, Summarizer.tool_context_key: tool_context}

    def _log_final_response(self, response: str) -> str:
        self.log_entry.final_response = response
        return response
