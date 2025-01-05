from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, Message
from app.core.llm import cohere_client as co
from cohere.types import CitationOptions
from typing import List
import json

router = APIRouter()

async def generate_stream(messages: List[Message], context: List[str]):
    # print("messages :", messages)  # Debugging, can be removed
    try:
        documents = [{"id": str(idx + 1), "data": doc} for idx, doc in enumerate(context)] if context else []
        
        res = co.chat_stream(
            model="command-r-plus",
            messages=messages,
            documents=documents,
            temperature=0.3,
        )

        # Stream the response
        for event in res:
            if event:
                if event.type == "content-delta":
                    yield f"data: {event.delta.message.content.text}\n\n"

                elif event.type == "citation-start":
                    # Convert citations to a serializable format
                    print("citation-start: ",event.delta.message.citations)
                    citations = [
                        {
                            "start": event.delta.message.citations.start,
                            "end": event.delta.message.citations.end,
                            "text": event.delta.message.citations.text,
                            "document_id": event.delta.message.citations.sources[0].id,
                        }
                    ]
                    citation_data = {
                        "type": event.type,
                        "citations": citations
                    }
                    yield f"data: {json.dumps(citation_data)}\n\n"

            elif event.event_type == "stream-end":
                yield f"data: .\n\n"
                yield f"data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield f"data: [DONE]\n\n"

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            generate_stream(request.messages, request.context),
            media_type="text/event-stream"
        )
    else:
        try:
            documents = [{"id": str(idx + 1), "data": doc} for idx, doc in enumerate(request.context.split())] if request.context else []
            current_message = request.messages[-1].content
            message_with_context = current_message
            if request.context:
                message_with_context = f"Context: {request.context}\n\nQuestion: {message_with_context}"
            
            response = await co.chat(
                message=message_with_context,
                model='command',
                documents=documents  
            )
            return {"response": response.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))