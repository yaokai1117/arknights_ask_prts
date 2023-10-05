from pydantic import BaseModel

# Data models for communicate with this chat API.
class AskPrtsRequest(BaseModel):
    content: str
