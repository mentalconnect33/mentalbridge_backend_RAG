# Mental Health Support AI Backend

A powerful Python backend service powering the ConnectX mental health support platform. This backend provides AI-powered conversations, resource recommendations, and clinical information through a RESTful API.

## Features

### AI-Powered Conversations
- Natural language processing for mental health inquiries
- Empathetic responses with supportive guidance
- Contextually relevant information delivery
- Well-formatted responses using Markdown styling

### Retrieval Augmented Generation (RAG)
- Context-aware responses enhanced with relevant information
- Semantic search for articles and clinical resources
- Personalized and accurate content delivery
- Integration with vector database for efficient retrieval

### Resource Recommendations
- Contextual article suggestions based on user queries
- Mental health clinic recommendations
- Customized resource matching based on user needs
- Structured data format for easy frontend rendering

### API Endpoints
- `/api/chat` - Main conversation endpoint with RAG capabilities
- `/api/health` - Service health check endpoint
- Clean response structure with formatted content

### Text Formatting
- Consistent response formatting with proper structure
- Clean bullet points and section headings
- Markdown compatibility for frontend rendering
- Enhanced readability with proper spacing and indentation

## Technology Stack

### Core Technologies
- **Python 3.9+** - Core programming language
- **FastAPI** - Modern, high-performance web framework
- **OpenAI API** - Language model integration for response generation
- **Vector Database** - Storage for embeddings and semantic search

### Key Libraries
- **Pydantic** - Data validation and settings management
- **Regex** - Text processing and formatting
- **OpenAI** - API client for language model access
- **CORS Middleware** - Cross-Origin Resource Sharing support

### Development Tools
- **Uvicorn** - ASGI server for local development and deployment
- **Logging** - Comprehensive logging system
- **Environment Variables** - Configuration management

## Architecture

The backend follows a modular architecture with these key components:

1. **API Layer** (`/app/api`)
   - Routes and endpoint definitions
   - Request/response models
   - Input validation

2. **Core Logic** (`/app/core`)
   - RAG implementation for retrieval-based responses
   - LLM integration for natural language generation
   - Vector store for semantic search capabilities

3. **Configuration** (`/app/config.py`)
   - Environment variable management
   - System settings
   - API keys and security settings

## Getting Started

### Prerequisites
- Python 3.9 or higher
- OpenAI API key

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/connectx-backend.git
   cd connectx-backend
   ```

2. Create a virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_CHAT_MODEL=gpt-4
   APP_NAME=Mental Health Support API
   MEDICAL_DISCLAIMER=This AI provides general information and support but is not a substitute for professional medical advice, diagnosis, or treatment.
   ```

5. Start the development server
   ```
   python -m app.main
   ```

6. The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at `http://localhost:8000/docs`.

### Main Endpoints

#### POST /api/chat
Process a user query and return AI-generated responses with relevant resources.

**Request Body:**
```json
{
  "query": "I've been feeling anxious lately",
  "chat_history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

**Response:**
```json
{
  "response": "I understand anxiety can be difficult to manage...",
  "formatted_data": {
    "metadata": {
      "sections": ["Understanding Anxiety", "Recommendations"],
      "clinic_references": [1, 2],
      "article_references": [3]
    }
  },
  "articles": [...],
  "clinics": [...]
}
```

#### GET /api/health
Check if the API is operational.

**Response:**
```json
{
  "status": "ok"
}
```

## Development

### Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   ├── rag.py
│   │   └── vector_store.py
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── .env
└── requirements.txt
```

### Adding New Features
1. Define data models in `app/api/models.py`
2. Create route handlers in `app/api/routes.py`
3. Implement business logic in the appropriate core module
4. Update documentation and tests

## Deployment

### Using Docker (Recommended)
1. Build the Docker image
   ```
   docker build -t connectx-backend .
   ```

2. Run the container
   ```
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key connectx-backend
   ```

### Standalone Deployment
1. Install production dependencies
   ```
   pip install gunicorn
   ```

2. Start the server
   ```
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## License
All Rights Reserved (aka not open source)

## Acknowledgements
- OpenAI for providing the language model capabilities
- FastAPI team for the excellent web framework
- All contributors to the open-source libraries used in this project
