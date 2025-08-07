# Recipe Recommendation MVP

A FastAPI-based recipe recommendation system that uses Pinecone for vector storage and OpenAI for AI-powered recipe generation.

## Features

- **PDF Recipe Upload**: Extract and store recipes from PDF files
- **Vector Search**: Semantic search for recipes using Pinecone
- **AI-Powered Recommendations**: Generate personalized recipes using OpenAI
- **User Management**: Store user profiles and preferences
- **Conversation History**: Track user interactions and recipe recommendations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file based on `env.example`:

```bash
cp env.example .env
```

Fill in your API keys:

- `PINECONE_API_KEY`: Your Pinecone API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `MONGODB_URI`: Your MongoDB connection string

### 3. PDF Recipe Upload

#### Option 1: Command Line Script

1. Create a directory for your PDF recipe files:

```bash
mkdir pdf_recipes
```

2. Place your PDF recipe files in the `pdf_recipes` directory

3. Run the upload script:

```bash
python upload_recipes_from_pdf.py --pdf-dir pdf_recipes
```

#### Option 2: API Endpoint

Use the `/upload-pdf-recipes` endpoint to upload PDF files via API:

```bash
curl -X POST "http://localhost:8000/upload-pdf-recipes" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_recipe_file.pdf"
```

### 4. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`

## API Endpoints

### Recipe Management

- `POST /upload-pdf-recipes`: Upload recipes from PDF files
- `GET /search?query={query}&top_k={number}`: Search recipes by semantic similarity
- `GET /recipes`: Get all stored recipes

### User Management

- `GET /users/{user_id}`: Get user profile
- `POST /users`: Create new user
- `PUT /users/{user_id}`: Update user profile

## PDF Recipe Format

The system can extract recipes from PDF files with the following information:

- Recipe name
- Ingredients list
- Cooking instructions
- Cuisine type
- Difficulty level
- Cooking time
- Number of servings
- Description

## Vector Search

The system uses Pinecone for semantic search, allowing you to find recipes based on:

- Ingredient names
- Cuisine types
- Cooking methods
- Recipe descriptions

## Development

### Project Structure

```
cvp-lite/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── vector_store.py
│   ├── pdf_processor.py
│   └── routes/
│       ├── __init__.py
│       ├── recipes.py
│       └── users.py
├── data/
├── pdf_recipes/          # Place your PDF files here
├── upload_recipes_from_pdf.py
├── main.py
└── requirements.txt
```

### Adding New Recipes

1. **Via PDF**: Place PDF files in the `pdf_recipes` directory and run the upload script
2. **Via API**: Use the upload endpoint to process PDF files
3. **Manual**: Use the vector store methods directly in your code

## Troubleshooting

### Common Issues

1. **PDF Processing Errors**: Ensure your PDF files contain readable text (not just images)
2. **API Key Issues**: Verify your Pinecone and OpenAI API keys are correctly set
3. **Memory Issues**: Large PDF files may require more memory; consider processing smaller files

### Logs

Check the application logs for detailed error information and processing status.

## License

This project is licensed under the MIT License.
