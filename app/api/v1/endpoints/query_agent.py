from fastapi import APIRouter, HTTPException
from typing import Optional, List
from app.core.llm import cohere_client
from app.schemas.chat import AgentQuery, AgentResponse
import json

router = APIRouter()

async def analyze_query(
    query: str,
) -> AgentResponse:
    """
    Analyze the query to determine if it needs vector search for job-related information
    or can be answered with general knowledge.
    """
    system_prompt = """You are an agent that determines if a user query needs job search capabilities.
    Analyze the query and decide if it:
    1. Needs job search (queries about specific jobs, companies, positions, salaries, etc.)
    2. Can be answered with general knowledge (questions about career advice, resume tips, interview preparation, etc.)
    
    Return your decision in JSON format:
    {
        "needs_vector_search": boolean,
        "reasoning": "brief explanation",
        "modified_query": "optional modified query for better search results"
    }
    
    Examples:
    - "Find me software engineering jobs in San Francisco" -> needs_vector_search: true
    - "How do I prepare for a behavioral interview?" -> needs_vector_search: false
    - "What are typical salaries for data scientists?" -> needs_vector_search: true
    - "Tips for writing a cover letter" -> needs_vector_search: false
    """
    
    # Include conversation history if available
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": query})

    schema = {
    "type": "object",
    "properties": {
        "needs_vector_search": {"type": "boolean"},
        "reasoning": {"type": "string"},
        "modified_query": {"type": "string"}
    },
    "required": [ "needs_vector_search", "reasoning" ]
}
    
    try:
        response = cohere_client.chat(
            model="command-r-plus",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object", "schema": schema}
        )
       
        raw_content = response.message.content
        if raw_content and isinstance(raw_content, list):
            # Get the text field from the first content item
            json_text = raw_content[0].text
            parsed_content = json.loads(json_text)  # Convert JSON string to dictionary
        else:
            raise ValueError("Invalid response content format.")

        return AgentResponse(
            needs_vector_search=parsed_content.get("needs_vector_search", True),
            reasoning=parsed_content.get("reasoning", ""),
            modified_query=parsed_content.get("modified_query", query)
        )
        
        
    except Exception as e:
        # Default to using vector search if there's an error
        return AgentResponse(
            needs_vector_search=True,
            reasoning=f"Error in analysis, defaulting to vector search: {str(e)}",
            modified_query=query
        )

@router.post("/analyze", response_model=AgentResponse)
async def analyze_query_endpoint(query_request: AgentQuery):
    """
    Endpoint to analyze a query for vector search requirements.
    """
    try:
        result = await analyze_query(
            query_request.query
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing query: {str(e)}"
        )