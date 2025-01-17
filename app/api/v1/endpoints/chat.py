from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, Message
from app.core.llm import cohere_client as co
from typing import List, AsyncGenerator
import json
import asyncio

router = APIRouter()

async def generate_stream(messages: List[Message], context: List[str]) -> AsyncGenerator[str, None]:
    try:
        documents = [{"id": str(idx + 1), "data": doc} for idx, doc in enumerate(context)] if context else []
        
        res = co.chat_stream(
            model="command-r-plus",
            messages=messages,
            documents=documents,
            temperature=0.3,
        )

        async def wrap_generator():
            try:
                for event in res:
                    if event:
                        if event.type == "content-delta":
                            yield f"data: {json.dumps(event.delta.message.content.text)}\n\n"
                            # await asyncio.sleep(0.01)
                        elif event.type == "citation-start":
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
                            await asyncio.sleep(0.01)
                    elif event.event_type == "stream-end":
                        yield "data: .\n\n"
                        yield "data: [DONE]\n\n"
            except GeneratorExit:
                # Properly handle generator cleanup
                if hasattr(res, 'close'):
                    res.close()
                return
            except Exception as e:
                print(f"Stream generation error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"
                return

        async for chunk in wrap_generator():
            yield chunk

    except Exception as e:
        print(f"Outer stream error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        response = StreamingResponse(
            generate_stream(request.messages, request.context),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': 'https://jobs-chatbot.vercel.app',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        
        return response
        
    except Exception as e:
        print(f"Chat stream endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=str(e),
            headers={
                'Access-Control-Allow-Origin': 'https://jobs-chatbot.vercel.app',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        