from typing import List, Dict, Any, Optional
from app.utils.supabase import supabase
from app.utils.embeddings import get_embedding, format_embedding_for_postgres, cosine_similarity
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    @staticmethod
    async def search_articles(query: str, top_k: int = settings.MAX_ARTICLE_RESULTS) -> List[Dict[str, Any]]:
        """Search for relevant articles using vector similarity."""
        try:
            query_embedding = get_embedding(query)
            embedding_str = format_embedding_for_postgres(query_embedding)
            query = f"""
            SELECT * FROM search_article_sections('{embedding_str}', {settings.SIMILARITY_THRESHOLD}, {top_k});
            """
            
            try:
                sections_response = supabase.rpc(
                    "search_article_sections", 
                    {
                        "query_embedding": embedding_str,
                        "match_threshold": settings.SIMILARITY_THRESHOLD,
                        "match_count": top_k
                    }
                ).execute()
                sections_data = sections_response.data if sections_response else []
                results = []
                
                for section in sections_data:
                    article_id = section["article_id"]
                    article_response = supabase.table("articles").select("*").eq("id", article_id).single().execute()
                    if not article_response.data:
                        continue

                    article = article_response.data
                    author_response = supabase.table("article_authors").select(
                        "authors(name, title, avatar)"
                    ).eq("article_id", article_id).single().execute()
                    
                    author = author_response.data["authors"] if author_response.data else None
                    
                    results.append({
                        "id": article_id,
                        "title": article["title"],
                        "category": article["category"], 
                        "section_title": section["section_title"],
                        "section_content": section["section_content"],
                        "author": author,
                        "similarity": section["similarity"],
                        "source_type": "section",
                        "read_time": article["read_time"]
                    })
                
                if results:
                    return results
                
            except Exception as e:
                print(f"pgvector search failed: {str(e)}")
            print("Falling back to manual similarity search")
            return await VectorStore.search_articles_fallback(query, top_k)
            
        except Exception as e:
            print(f"Error searching articles: {str(e)}")
            return []
    
    @staticmethod
    async def search_clinics(query: str, top_k: int = settings.MAX_CLINIC_RESULTS) -> List[Dict[str, Any]]:
        """Search for relevant clinics using vector similarity."""
        try:
            query_embedding = get_embedding(query)
            embedding_str = format_embedding_for_postgres(query_embedding)
            try:
                clinics_response = supabase.rpc(
                    "search_clinics",
                    {
                        "query_embedding": embedding_str,
                        "match_threshold": settings.SIMILARITY_THRESHOLD,
                        "match_count": top_k
                    }
                ).execute()
                
                clinics_data = clinics_response.data if clinics_response else []
                
                if clinics_data:
                    enhanced_clinics = []
                    for clinic in clinics_data:
                        clinic_id = clinic["clinic_id"]
                        specialties_response = supabase.table("clinic_specialties").select(
                            "specialties(name)"
                        ).eq("clinic_id", clinic_id).execute()
                        
                        specialties = [
                            item["specialties"]["name"] 
                            for item in specialties_response.data
                        ] if specialties_response.data else []

                        insurance_response = supabase.table("clinic_insurance").select(
                            "insurance_providers(name)"
                        ).eq("clinic_id", clinic_id).execute()
                        
                        insurance = [
                            item["insurance_providers"]["name"] 
                            for item in insurance_response.data
                        ] if insurance_response.data else []
                        
                        enhanced_clinics.append({
                            **clinic,
                            "specialties": specialties,
                            "insurance_accepted": insurance
                        })
                    
                    return enhanced_clinics
                    
            except Exception as e:
                print(f"pgvector clinic search failed: {str(e)}")
            return await VectorStore.search_clinics_fallback(query, top_k)
            
        except Exception as e:
            print(f"Error searching clinics: {str(e)}")
            return []

    @staticmethod
    async def search_articles_fallback(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fallback search for articles when vector search fails."""
        try:
            articles_response = supabase.table("articles").select("*").execute()
            articles = articles_response.data if articles_response.data else []
            query_embedding = get_embedding(query)
            scored_articles = []
            for article in articles:
                content_response = supabase.table("article_content").select("*").eq("article_id", article["id"]).single().execute()
                if not content_response.data:
                    continue
                
                content = content_response.data
                sections_response = supabase.table("article_sections").select("*").eq("article_id", article["id"]).execute()
                sections = sections_response.data if sections_response.data else []
    
                author_response = supabase.table("article_authors").select(
                    "authors(name, title, avatar)"
                ).eq("article_id", article["id"]).single().execute()
                author = author_response.data["authors"] if author_response.data else None
                title_sim = cosine_similarity(
                    get_embedding(article["title"]), 
                    query_embedding
                )
                intro_sim = cosine_similarity(
                    get_embedding(content["introduction"]), 
                    query_embedding
                )
                best_section = None
                best_section_sim = 0
                
                for section in sections:
                    section_sim = cosine_similarity(
                        get_embedding(section["title"] + " " + section["content"]),
                        query_embedding
                    )
                    if section_sim > best_section_sim:
                        best_section_sim = section_sim
                        best_section = section
                max_sim = max(title_sim, intro_sim, best_section_sim)
                
                scored_articles.append({
                    "id": article["id"],
                    "title": article["title"],
                    "category": article["category"],
                    "section_title": best_section["title"] if best_section else "Introduction",
                    "section_content": best_section["content"] if best_section else content["introduction"],
                    "author": author,
                    "similarity": max_sim,
                    "source_type": "section" if best_section else "article_content",
                    "read_time": article.get("read_time", "5 min") 
                })
            
            scored_articles.sort(key=lambda x: x["similarity"], reverse=True)
            return scored_articles[:top_k]
            
        except Exception as e:
            print(f"Error in fallback search: {str(e)}")
            return []

    @staticmethod
    async def search_clinics_fallback(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fallback search for clinics when vector search fails."""
        import re
        
        try:
            # Get all clinics
            clinics_response = supabase.table("clinics").select("*").execute()
            clinics = clinics_response.data if clinics_response.data else []
            
            if not clinics:
                print("No clinics found in database")
                return []
            
            keywords = set(re.findall(r'\w+', query.lower()))
            keywords_list = list(keywords)
    
            scored_clinics = []
            for clinic in clinics:
                clinic_text = f"{clinic['name']} {clinic.get('description', '')}".lower()
                clinic_keywords = set(re.findall(r'\w+', clinic_text))
                matches = len(keywords.intersection(clinic_keywords))
                specialties_response = supabase.table("clinic_specialties").select(
                    "specialties(name)"
                ).eq("clinic_id", clinic["id"]).execute()
                
                specialties = []
                if specialties_response.data:
                    for item in specialties_response.data:
                        if "specialties" in item and "name" in item["specialties"]:
                            specialties.append(item["specialties"]["name"])
                
                for specialty in specialties:
                    if any(kw in specialty.lower() for kw in keywords_list):
                        matches += 2  
                insurance_response = supabase.table("clinic_insurance").select(
                    "insurance_providers(name)"
                ).eq("clinic_id", clinic["id"]).execute()
                
                insurance = []
                if insurance_response.data:
                    for item in insurance_response.data:
                        if "insurance_providers" in item and "name" in item["insurance_providers"]:
                            insurance.append(item["insurance_providers"]["name"])
                if matches > 0 or "therapist" in query.lower() or "clinic" in query.lower():
                    scored_clinics.append({
                        "clinic_id": clinic["id"],
                        "name": clinic["name"],
                        "description": clinic.get("description", ""),
                        "location": clinic.get("location", ""),
                        "rating": clinic.get("rating", 0),
                        "accepting_new": clinic.get("accepting_new", False),
                        "specialties": specialties,
                        "insurance_accepted": insurance,
                        "similarity": 0.5 + (0.1 * matches)  # Simple scoring
                    })
            scored_clinics.sort(key=lambda x: x["similarity"], reverse=True)
            if not scored_clinics and ("therapist" in query.lower() or "clinic" in query.lower()):
                for clinic in clinics[:min(top_k, len(clinics))]:
                    specialties_response = supabase.table("clinic_specialties").select(
                        "specialties(name)"
                    ).eq("clinic_id", clinic["id"]).execute()
                    
                    specialties = []
                    if specialties_response.data:
                        for item in specialties_response.data:
                            if "specialties" in item and "name" in item["specialties"]:
                                specialties.append(item["specialties"]["name"])
                    
                    insurance_response = supabase.table("clinic_insurance").select(
                        "insurance_providers(name)"
                    ).eq("clinic_id", clinic["id"]).execute()
                    
                    insurance = []
                    if insurance_response.data:
                        for item in insurance_response.data:
                            if "insurance_providers" in item and "name" in item["insurance_providers"]:
                                insurance.append(item["insurance_providers"]["name"])
                    
                    scored_clinics.append({
                        "clinic_id": clinic["id"],
                        "name": clinic["name"],
                        "description": clinic.get("description", ""),
                        "location": clinic.get("location", ""),
                        "rating": clinic.get("rating", 0),
                        "accepting_new": clinic.get("accepting_new", False),
                        "specialties": specialties,
                        "insurance_accepted": insurance,
                        "similarity": 0.5  
                    })
            
            return scored_clinics[:top_k]
            
        except Exception as e:
            print(f"Error in clinics fallback search: {str(e)}")
            return []
