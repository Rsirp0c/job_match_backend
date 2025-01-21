from fastapi import APIRouter, HTTPException
from app.core.vector_store import pinecone_index
from app.schemas.chat import VectorQuery, VectorQueryResponse
from app.core.llm import cohere_client

router = APIRouter()

@router.post("/search", response_model=VectorQueryResponse)
async def search_vectors(query: VectorQuery):
    try:
        # Generate embedding for the query
        query_embedding = cohere_client.embed(
            texts=[query.query],
            model="embed-english-v3.0",
            input_type="search_query",
            embedding_types=['float']
        ).embeddings.float[0]
        
        # Search Pinecone
        search_response = pinecone_index.query(
            vector=query_embedding,
            filter=query.filter,
            top_k=query.top_k,
            include_metadata=True
        )
        
        # Convert Pinecone matches to the expected format
        formatted_matches = [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            } for match in search_response.matches
        ]
        
        return VectorQueryResponse(
            matches=formatted_matches,
            metadata={"total_matches": len(formatted_matches)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))