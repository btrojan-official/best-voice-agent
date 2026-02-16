from typing import List, Dict, Any
from datetime import datetime


class CustomerSupportTools:
    """Tools available to the customer support agent."""
    
    @staticmethod
    def get_current_time() -> str:
        """Get the current date and time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def log_information(category: str, value: str) -> Dict[str, str]:
        """
        Log a piece of information gathered from the customer.
        
        Args:
            category: The type of information (e.g., "issue_type", "customer_name")
            value: The actual information value
        
        Returns:
            Confirmation dictionary
        """
        return {
            "status": "logged",
            "category": category,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def search_knowledge_base(query: str) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
        
        Returns:
            Search results dictionary
        """
        return {
            "status": "success",
            "query": query,
            "results": [
                "This is a placeholder for knowledge base integration.",
                "In production, this would search actual documentation."
            ]
        }


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get list of available tools in OpenAI function calling format.
    
    Returns:
        List of tool definitions
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get the current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "log_information",
                "description": "Log a piece of information gathered from the customer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "The type of information (e.g., 'issue_type', 'customer_name')"
                        },
                        "value": {
                            "type": "string",
                            "description": "The actual information value"
                        }
                    },
                    "required": ["category", "value"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
