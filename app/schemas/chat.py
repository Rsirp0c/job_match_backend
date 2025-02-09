from pydantic import BaseModel
from typing import List, Optional, Dict, Union

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = True
    context: Optional[Union[List[Dict], str]] = None

class VectorQuery(BaseModel):
    query: str
    filter: Optional[Dict] = None
    top_k: int = 5

class VectorQueryResponse(BaseModel):
    matches: List[Dict]
    metadata: Optional[Dict] = None

class AgentQuery(BaseModel):
    query: str

class AgentResponse(BaseModel):
    needs_vector_search: bool

class CombinedResponse(BaseModel):
    analysis: AgentResponse
    vector_results: List[Dict] = []  # Using List[Dict] to match the vector search response format