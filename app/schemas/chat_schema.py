from pydantic import BaseModel


class ChatRequest(BaseModel):
	question: str
	analyst_mode: bool = False


class ChatResponse(BaseModel):
	response: str
