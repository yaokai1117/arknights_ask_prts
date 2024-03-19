from pydantic import BaseModel
from typing import Tuple

# LLM data models.
class Message(BaseModel):
    role: str
    content: str

    def to_tuple(self) -> Tuple[str, str]:
        return (self.role, self.content)