from pydantic import BaseModel

# LLM data models.
class Message(BaseModel):
    role: str
    content: str
