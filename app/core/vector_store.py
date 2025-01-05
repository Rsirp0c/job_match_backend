import os
from pinecone import Pinecone
from app.core.config import settings

def init_pinecone():
    pc = Pinecone(
        api_key=settings.PINECONE_API_KEY
    )
    
    # Get the index by name
    return pc.Index(settings.PINECONE_INDEX_NAME)

pinecone_index = init_pinecone()