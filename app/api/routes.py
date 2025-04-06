from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Union
from app.api.models import ChatResponse, ChatRequest
from app.core.rag import RAG
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()

def enhance_response_formatting(text: str) -> Dict[str, Any]:
    """
    Process the response to improve its formatting and extract structured data.
    This helps the frontend display the content in a more organized way.
    
    Returns a dictionary with the formatted text and extracted metadata.
    """
    if not isinstance(text, str):
        logger.warning(f"Response is not a string: {type(text)}. Converting to string.")
        text = str(text)
    
    text = re.sub(r'(?m)^[-*] ', '• ', text)  
    text = re.sub(r'(?m)^(•)(?!\s)', r'\1 ', text) 
    text = re.sub(r'(?m)^(\d+)\.\s*\*?\*?\[Clinic (\d+)\]\*?\*?:?\s*', r'\1. **[Clinic \2]**: ', text)
    text = re.sub(r'(?m)^(\d+)\.\s*\*?\*?\[Article (\d+)\]\*?\*?:?\s*', r'\1. **[Article \2]**: ', text)
    
    # Ensure clinic bullet points are properly indented
    text = re.sub(r'(?m)^((\d+)\. \*\*\[Clinic \d+\]\*\*:.+\n)(?=•)', r'\1   ', text)
    text = re.sub(r'(?m)^([A-Z][A-Za-z\s]+):\s*$', r'**\1:**', text)
    text = re.sub(r'(?m)(•\s.+)\n(?=\d+\.\s+\*\*\[Clinic)', r'\1\n\n', text)
    
    clinic_pattern = r'(?:\*\*\[Clinic (\d+)\]\*\*|\[Clinic (\d+)\])'
    clinic_refs = re.findall(clinic_pattern, text)
    clinic_references = [int(c[0] or c[1]) for c in clinic_refs if c[0] or c[1]]
    article_pattern = r'(?:\*\*\[Article (\d+)\]\*\*|\[Article (\d+)\])'
    article_refs = re.findall(article_pattern, text)
    article_references = [int(a[0] or a[1]) for a in article_refs if a[0] or a[1]]
    
    section_pattern = r'\*\*([^:*]+):\*\*'
    sections = re.findall(section_pattern, text)
    
    clinic_entries = []
    clinic_entry_pattern = r'(\d+)\.\s+\*\*\[Clinic (\d+)\]\*\*:\s+(.+?)(?=\n\n\d+\.\s+\*\*\[Clinic|\n\n\*\*|\Z)'
    clinic_matches = re.findall(clinic_entry_pattern, text, re.DOTALL)
    
    for match in clinic_matches:
        number, clinic_id, content = match
        bullet_items = re.findall(r'•\s+([^•]+?)(?=\n\s*•|\Z)', content, re.DOTALL)
        bullet_items = [item.strip() for item in bullet_items]
        
        clinic_entries.append({
            "number": int(number),
            "clinic_id": int(clinic_id),
            "name": content.split('\n')[0].strip(),
            "details": bullet_items
        })
    
    structured_data = {
        "formatted_text": text,
        "metadata": {
            "clinic_references": clinic_references,
            "article_references": article_references,
            "sections": sections,
            "clinic_entries": clinic_entries
        }
    }
    
    return structured_data

@router.post("/chat")
async def chat(request: Union[Dict[str, Any], ChatRequest]):
    try:
        if isinstance(request, dict):
            query = request.get("query", "")
            chat_history_raw = request.get("chat_history", [])
        else:
            query = request.query
            chat_history_raw = request.chat_history
        
        chat_history = [
            {"role": msg.get("role", "user") if isinstance(msg, dict) else msg.role, 
             "content": msg.get("content", "") if isinstance(msg, dict) else msg.content}
            for msg in chat_history_raw
        ]
        
        response, articles, clinics = await RAG.process_query(
            query=query,
            chat_history=chat_history
        )
        if not isinstance(response, str):
            logger.warning(f"Response from RAG is not a string: {type(response)}. Converting to string.")
            response = str(response)
        enhanced_response = enhance_response_formatting(response)
        return {
            "response": enhanced_response["formatted_text"],
            "formatted_data": enhanced_response["metadata"],
            "articles": articles,
            "clinics": clinics
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
