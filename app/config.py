import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.APP_NAME = "Mental Health RAG API"
        
        # OpenAI
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"  
        self.OPENAI_CHAT_MODEL = "gpt-4"  
        
        # Supabase
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        
        # Vector settings
        self.EMBEDDING_DIM = 1536
        self.SIMILARITY_THRESHOLD = 0.75
        
        # RAG settings
        self.MAX_ARTICLE_RESULTS = 3
        self.MAX_CLINIC_RESULTS = 3
        
        # Disclaimers
        self.MEDICAL_DISCLAIMER = ("I'm an AI assistant designed to provide information and support, "
                                 "not to replace professional medical advice. Please consult with a "
                                 "healthcare provider for proper diagnosis and treatment.")

settings = Settings()
