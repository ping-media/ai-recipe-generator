#!/usr/bin/env python3
"""
Setup script for Recipe Recommendation MVP
"""
import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists("env.example"):
        try:
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from template")
            print("⚠️  Please update .env with your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "main.py",
        "requirements.txt",
        "app/__init__.py",
        "app/config.py",
        "app/models.py",
        "app/database.py",
        "app/vector_store.py",
        "app/ai_service.py",
        "app/routes/__init__.py",
        "app/routes/users.py",
        "app/routes/recipes.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Recipe Recommendation MVP")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check required files
    if not check_required_files():
        print("\n❌ Setup failed: Missing required files")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Setup failed: Could not create .env file")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your API keys:")
    print("   - MONGODB_URI (MongoDB Atlas connection string)")
    print("   - PINECONE_API_KEY (Pinecone API key)")
    print("   - PINECONE_ENVIRONMENT (Pinecone environment)")
    print("   - OPENAI_API_KEY (OpenAI API key)")
    print("\n2. Run the application:")
    print("   python main.py")
    print("\n3. Test the API:")
    print("   python test_api.py")
    print("\n4. View API documentation:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main() 