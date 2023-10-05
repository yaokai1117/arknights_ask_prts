from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

# Planner data models.
class PlannerOutputType(str, Enum):
    unrelated = 'unrelated'
    solvable_by_tool = 'solvable_by_tool'

class ToolType(str, Enum):
    game_data_graph_ql = 'game_data_graph_ql'
    bilibili_search = 'bilibili_search'

class PlannerOutput(BaseModel):
    succeeded: bool
    error: Optional[str] = None
    type: Optional[PlannerOutputType] = None
    tool_type: Optional[ToolType] = None
    tool_input: Optional[List[str]] = None

    class Config:  
        use_enum_values = True
