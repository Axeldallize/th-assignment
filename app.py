from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import pandas as pd
import re

from config import Config
from llm_client import AnthropicClient, LLMError
from database import DatabaseManager, DatabaseError
# We will replace this with a proper import later
from prompt_templates import TEXT_TO_SQL_PROMPT 

def _extract_sql_from_response(raw_llm_output: str) -> str:
    """
    Extracts a SQL query from the LLM's raw output by first looking for a
    markdown block, then falling back to the last SELECT statement.
    """
    # First, try to find a markdown ```sql ... ``` block
    sql_match = re.search(r"```sql\n(.*?)\n```", raw_llm_output, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()

    # If no markdown block, find the last SELECT statement in the text.
    # This is more robust against conversational AI responses.
    select_match = re.search(r'.*(SELECT .*)$', raw_llm_output, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()
    
    # If no SQL is found, return the original raw output for the validator to handle.
    return raw_llm_output.strip()

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Database Query and Analysis System",
    description="AI-powered system for querying and analyzing database content using natural language",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
try:
    llm_client = AnthropicClient()
    db_manager = DatabaseManager()
except (LLMError, DatabaseError) as e:
    logger.critical(f"Failed to initialize clients on startup: {e}")
    # In a real app, you might want to exit or have a retry mechanism
    llm_client = None
    db_manager = None

# Pydantic models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

# Get schema once at startup
SCHEMA_STRING = ""
if db_manager:
    try:
        SCHEMA_STRING = db_manager.get_formatted_schema()
        logger.info("Successfully loaded database schema.")
    except DatabaseError as e:
        logger.error(f"Could not load database schema on startup: {e}")
        SCHEMA_STRING = "Error: Database schema could not be loaded."

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Database Query and Analysis System",
        "description": "Ask analytical questions about the database using natural language",
        "endpoints": {
            "/query": "POST - Submit a natural language question about the database"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Database Query System is running"}

@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Processes a natural language question through a conversational AI workflow
    to generate and execute SQL, and return a final answer.
    """
    if not llm_client or not db_manager or SCHEMA_STRING.startswith("Error"):
        raise HTTPException(status_code=503, detail="System is not available due to initialization errors.")

    # We will replace this with a proper prompt from prompt_templates.py
    # For now, this is a placeholder to show the structure.
    system_prompt = TEXT_TO_SQL_PROMPT.format(schema=SCHEMA_STRING)

    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.question}
    ]

    try:
        # Step 1: Get raw response and extract SQL
        raw_llm_output = await llm_client.get_response(conversation)
        sql_query = _extract_sql_from_response(raw_llm_output) # This function makes our app more robust to hallucinations

        conversation.append({"role": "assistant", "content": sql_query})
        logger.info(f"Extracted SQL: {sql_query}")

        # Step 2: Execute SQL with self-correction (this is to prevent the LLM from hallucinating)
        try:
            # First attempt
            df = db_manager.execute_query(sql_query)
            result_for_llm = "Query executed successfully. Here is the data in CSV format:\n" + df.to_csv(index=False)
        except DatabaseError as e:
            logger.warning(f"SQL execution failed. Attempting self-correction. Error: {e}")
            # This is the self-correction part
            correction_prompt = f"The query failed with the following error: {e}. Please review the schema and your query, then provide the corrected SQL query only."
            conversation.append({"role": "user", "content": correction_prompt})
            
            # Get new response and extract corrected SQL
            raw_llm_output = await llm_client.get_response(conversation)
            sql_query = _extract_sql_from_response(raw_llm_output)

            conversation.append({"role": "assistant", "content": sql_query})
            logger.info(f"Extracted corrected SQL: {sql_query}")
            
            # Second attempt
            df = db_manager.execute_query(sql_query)
            result_for_llm = "Query executed successfully on the second attempt. Here is the data in CSV format:\n" + df.to_csv(index=False)

        # Step 3: Get final analysis from LLM
        analysis_prompt = f"""Here is the data you requested in CSV format:
{result_for_llm}

Your task is now to act as a data analyst and provide a clear, human-readable answer to the original question. Do NOT generate any more SQL."""
        conversation.append({"role": "user", "content": analysis_prompt})
        
        final_answer = await llm_client.get_response(conversation)
        
        return QueryResponse(answer=final_answer)

    except (LLMError, DatabaseError) as e:
        logger.error(f"A critical error occurred in the query process: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=Config.HOST, port=Config.PORT, reload=True) 