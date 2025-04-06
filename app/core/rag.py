from typing import List, Dict, Any, Tuple
from app.core.vector_store import VectorStore
from app.core.llm import LLM
import logging

logger = logging.getLogger(__name__)

class RAG:
    @staticmethod
    async def process_query(
        query: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process a user query through the RAG system and return:
        1. The generated response
        2. Relevant articles
        3. Relevant clinics
        """
        if chat_history is None:
            chat_history = []
        
        try:
            query_analysis = await LLM.analyze_mental_health_query(query)
            articles = await VectorStore.search_articles(query)
            is_clinic_related = False
            if query_analysis.get("seeking_clinical_help", False) or \
               query_analysis.get("primary_need") == "clinical":
                is_clinic_related = True

            clinic_keywords = [
                "therapist", "clinic", "doctor", "professional", "psychiatrist", 
                "psychologist", "counselor", "therapy", "appointment", "provider",
                "specialist", "mental health services", "treatment center",
                "insurance", "healthcare", "practitioner", "consultation"
            ]
            
            if not is_clinic_related:
                for keyword in clinic_keywords:
                    if keyword in query.lower():
                        is_clinic_related = True
                        break
            clinics = []
            if is_clinic_related:
                print("Query appears to be clinic-related, retrieving clinic information")
                clinics = await VectorStore.search_clinics(query)
            else:
                print("Query does not appear to be clinic-related, skipping clinic search")

            response = await LLM.generate_response(
                query=query,
                articles=articles,
                clinics=clinics,
                chat_history=chat_history
            )
            print(f"Articles found: {len(articles)}")
            print(f"Clinics found: {len(clinics)}")
            return response, articles, clinics
            
        except Exception as e:
            logger.error(f"Error in RAG processing: {str(e)}")
            error_response = (
                "I apologize, but I encountered an error while processing your request. "
                "Please try again with a different question or rephrase your current one."
            )
            return error_response, [], []
