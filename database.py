"""
Database utilities for PostgreSQL connection and schema management.
"""

import logging
import re
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from config import Config

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self):
        """Initialize database connection."""
        self.database_url = Config.get_database_url()
        self.engine = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {str(e)}")
    
    def get_formatted_schema(self) -> str:
        """
        Get database schema information formatted for LLM prompts.
        
        Returns:
            Formatted schema string with tables, columns, and relationships
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names(schema="public")
            
            schema_parts = []
            
            for table in tables:
                columns = inspector.get_columns(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                # Format table info
                column_info = []
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "" if col['nullable'] else " NOT NULL"
                    column_info.append(f"  {col['name']} ({col_type}){nullable}")
                
                table_info = f"Table: {table}\n" + "\n".join(column_info)
                
                # Add foreign key info
                if foreign_keys:
                    fk_info = []
                    for fk in foreign_keys:
                        fk_info.append(f"  FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                    table_info += "\n" + "\n".join(fk_info)
                
                schema_parts.append(table_info)
            
            return "\n\n".join(schema_parts)
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return "Schema information unavailable"
    
    def validate_query(self, query: str) -> bool:
        """
        Validate that a query is safe to execute.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query is safe, False otherwise
        """
        # Basic validation - only allow SELECT statements
        query_clean = query.strip().upper()
        
        # Must start with SELECT
        if not query_clean.startswith('SELECT'):
            logger.warning(f"Query validation failed: Not a SELECT statement")
            return False
        
        # Check for dangerous keywords
        dangerous_keywords = [
            'DELETE', 'DROP', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_clean:
                logger.warning(f"Query validation failed: Contains dangerous keyword '{keyword}'")
                return False
        
        return True
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as pandas DataFrame.
        
        Args:
            query: SQL query to execute
            
        Returns:
            DataFrame with query results
            
        Raises:
            DatabaseError: If query execution fails
        """
        if not self.validate_query(query):
            raise DatabaseError("Query validation failed - potentially unsafe query")
        
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(text(query), conn)
                logger.info(f"Query executed successfully, returned {len(result)} rows")
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            raise DatabaseError(f"Query execution failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise DatabaseError(f"Unexpected error: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False 