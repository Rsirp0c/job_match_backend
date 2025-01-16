from fastapi import APIRouter, HTTPException
from typing import Optional, List
from app.core.llm import cohere_client
from app.core.vector_store import pinecone_index
from app.schemas.chat import AgentQuery, AgentResponse, CombinedResponse

import asyncio
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


async def get_vector_search(query: str):
    """Perform vector search asynchronously"""
    try:
        # Generate embedding
        query_embedding = cohere_client.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query",
            embedding_types=['float']
        ).embeddings.float[0]
        
        # Search Pinecone
        search_response = pinecone_index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            } for match in search_response.matches
        ]
    except Exception as e:
        print(f"Vector search error: {str(e)}")
        return []


async def analyze_and_search(query: str) -> CombinedResponse:
    """
    Combines query analysis and vector search into a single operation
    """
    # Run analysis and vector search concurrently
    analysis_task = analyze_query(query)
    vector_task = get_vector_search(query)
    
    analysis_result, vector_results = await asyncio.gather(
        analysis_task,
        vector_task
    )
    
    return CombinedResponse(
        analysis=analysis_result,
        vector_results=vector_results if analysis_result.needs_vector_search else []
    )

@router.post("/analyze_and_search", response_model=CombinedResponse)
async def combined_analysis_endpoint(query_request: AgentQuery):
    """
    Combined endpoint for query analysis and vector search
    """
    try:
        result = await analyze_and_search(query_request.query)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )