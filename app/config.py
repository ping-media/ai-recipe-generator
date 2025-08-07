import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE: str = "recipe_db"
    MONGODB_COLLECTION: str = "users"
    
    # Pinecone Configuration (New API)
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "recipes-db")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"  # Using GPT-4o for better recipe generation and reasoning
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Application Configuration
    APP_NAME: str = "Recipe Recommendation MVP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

# Create settings instance
settings = Settings() 