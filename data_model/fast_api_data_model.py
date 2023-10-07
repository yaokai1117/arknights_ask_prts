from pydantic import BaseModel
from typing import Optional

# Data models for communicate with this chat API.
class AskPrtsRequest(BaseModel):
    content: str
    session_id: Optional[str] = None

class AskPrtsReponse(BaseModel):
    content: str
    session_id: str
