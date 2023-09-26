from utils import llm_client, Message

class Processor():
    def process(self, question: str) -> str:
        message = Message(role='user', content=question)
        return llm_client.send([message])
