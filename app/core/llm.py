from typing import List, Dict, Any
import openai
import json
import re
from app.config import settings

class LLM:
    @staticmethod
    async def generate_response(
        query: str, 
        articles: List[Dict[str, Any]], 
        clinics: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a response using the OpenAI API with context from articles and clinics."""
        if chat_history is None:
            chat_history = []

        article_context = ""
        if articles:
            article_context = "Relevant article information:\n\n"
            for i, article in enumerate(articles, 1):
                if article.get("source_type") == "section":
                    article_context += f"[Article {i}] \"{article['title']}\" (Category: {article['category']})\n"
                    article_context += f"• Section: {article['section_title']}\n"
                    article_context += f"• Content: {article['section_content'][:500]}...\n\n"
                else:
                    article_context += f"[Article {i}] \"{article['title']}\" (Category: {article['category']})\n"
                    content_type = article.get('content_type', 'content')
                    article_context += f"• {content_type.capitalize()}: {article['content'][:500]}...\n\n"
    
        clinic_context = ""
        if clinics:
            clinic_context = "Relevant mental health clinic information:\n\n"
            for i, clinic in enumerate(clinics, 1):
                clinic_context += f"[Clinic {i}] {clinic['name']}\n"
                clinic_context += f"• Description: {clinic['description']}\n"
                clinic_context += f"• Location: {clinic['location']}\n"
                clinic_context += f"• Rating: {clinic['rating']} stars\n"
                clinic_context += f"• Accepting new patients: {'Yes' if clinic['accepting_new'] else 'No'}\n"
                clinic_context += f"• Specialties: {', '.join(clinic['specialties'])}\n"
                clinic_context += f"• Insurance accepted: {', '.join(clinic['insurance_accepted'])}\n\n"
        
        context = ""
        if article_context:
            context += article_context
        if clinic_context:
            context += clinic_context

        system_message = f"""
        You are an empathetic mental health assistant designed to provide clearly formatted responses.

        CRITICAL FORMATTING REQUIREMENTS:
        • Structure your response with distinct, separated sections
        • ALWAYS present clinic information in a clear, numbered list format
        • Each clinic must be on its own line with a clear number (1., 2., 3.)
        • After each clinic name, list details in bullet point format with proper spacing
        • Put a blank line between each clinic listing
        • For any lists, use proper bullet points (•) with consistent spacing
        • Format section headings in bold with a colon (e.g., **Clinic Recommendations:**)
        
        CLINIC FORMATTING EXAMPLE:
        **Clinic Recommendations:**
        
        1. **[Clinic 1]**: Center Name
           • Description: Brief description
           • Location: Address
           • Specialties: List of specialties
        
        2. **[Clinic 2]**: Other Center
           • Description: Brief description
           • Location: Address
           • Specialties: List of specialties
        
        ADDITIONAL GUIDELINES:
        • Keep your response concise and structured
        • Use short paragraphs (3-4 lines maximum)
        • Begin with a brief empathetic acknowledgment
        • End with a simple supportive statement

        Important: {settings.MEDICAL_DISCLAIMER}
        """
        
        messages = [{"role": "system", "content": system_message.strip()}]
        for message in chat_history:
            messages.append({"role": message["role"], "content": message["content"]})
        user_message = f"User question: {query}"
        if context:
            user_message += f"\n\nContext information to use in your response:\n{context}"
        
        messages.append({"role": "user", "content": user_message})
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        raw_response = response.choices[0].message['content']
        formatted_response = LLM.format_response(raw_response)
        
        return formatted_response
    
    @staticmethod
    def format_response(text: str) -> str:
        """
        Post-process the response to ensure consistent formatting.
        This makes the text look cleaner and more structured in the frontend.
        This section was written by Claude AI as I was too lazy to write it.
        """
        # Replace dash or asterisk bullets with proper Unicode bullets
        text = re.sub(r'(?m)^[-*] ', '• ', text)
        
        # Ensure consistent spacing after bullets
        text = re.sub(r'(?m)^(•)(?!\s)', r'\1 ', text)
        
        # Format clinic and article references with proper spacing and styling
        text = re.sub(r'(?m)^(\d+)\.\s*\*?\*?\[Clinic (\d+)\]\*?\*?:?\s*', r'\1. **[Clinic \2]**: ', text)
        text = re.sub(r'(?m)^(\d+)\.\s*\*?\*?\[Article (\d+)\]\*?\*?:?\s*', r'\1. **[Article \2]**: ', text)
        
        # Ensure clinic bullet points are properly indented
        text = re.sub(r'(?m)^((\d+)\. \*\*\[Clinic \d+\]\*\*:.+\n)(?=•)', r'\1   ', text)
        
        # Make sure section headings are properly formatted
        text = re.sub(r'(?m)^([A-Z][A-Za-z\s]+):\s*$', r'**\1:**', text)
        
        # Ensure proper spacing between clinics
        text = re.sub(r'(?m)(•\s.+)\n(?=\d+\.\s+\*\*\[Clinic)', r'\1\n\n', text)
        
        # Ensure proper spacing after paragraphs before new sections
        text = re.sub(r'(?m)([^•].+)\n(?=\*\*[A-Z][a-zA-Z ]+:\*\*)', r'\1\n\n', text)
        
        return text

    @staticmethod
    async def analyze_mental_health_query(query: str) -> Dict[str, Any]:
        """
        Analyze the user query to determine relevant topics, emotional states,
        and if it might be seeking clinical recommendations.
        """
        system_message = """
        You are a mental health query analyzer. Given a user's message, identify:
        1. The primary mental health topics mentioned or implied
        2. The apparent emotional state of the user
        3. Whether the user seems to be seeking clinical recommendations
        4. Any concerning phrases that suggest immediate risk
        
        Return your analysis in JSON format with the following structure:
        {
            "topics": ["topic1", "topic2"],
            "emotional_state": "brief description of emotional state",
            "seeking_clinical_help": true/false,
            "risk_level": "none" | "low" | "medium" | "high",
            "primary_need": "information" | "support" | "resources" | "clinical"
        }
        
        Be thoughtful and nuanced in your analysis. Don't overstate risk levels, but be
        appropriately cautious with concerning language.
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ],
            temperature=0.3
        )
        
        try:
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            return {
                "topics": ["general mental health"],
                "emotional_state": "unknown",
                "seeking_clinical_help": False,
                "risk_level": "unknown",
                "primary_need": "information"
            }
