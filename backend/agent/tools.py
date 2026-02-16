from typing import List, Dict, Any
from datetime import datetime


class CustomerSupportTools:
    """Tools available to the customer support agent."""
    
    def __init__(self):
        self.gathered_information = {}
    
    @staticmethod
    def get_current_time() -> str:
        """Get the current date and time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_gathered_data(self, data_fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Save one or multiple pieces of information gathered from the customer.
        Use this tool IMMEDIATELY when customer provides any relevant information.
        You can save multiple fields at once for efficiency.
        
        Args:
            data_fields: Dictionary where keys are field titles (e.g., "order_id", "customer_name") 
                        and values are the information provided by the customer
        
        Returns:
            Confirmation dictionary with saved data and remaining fields
        """
        for field_key, field_value in data_fields.items():
            if field_value and field_value.strip():
                self.gathered_information[field_key] = field_value.strip()
        
        return {
            "status": "saved",
            "saved_fields": data_fields,
            "total_gathered": len(self.gathered_information),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_gathered_information(self) -> Dict[str, str]:
        """Get all currently gathered information."""
        return self.gathered_information.copy()


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
                "name": "save_gathered_data",
                "description": "Save one or multiple pieces of customer information. Use IMMEDIATELY when customer provides data. You can save multiple fields at once (e.g., {\"order_id\": \"AB12CD\", \"customer_name\": \"John\"}).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_fields": {
                            "type": "object",
                            "description": "Dictionary of field_name: value pairs to save (e.g., {\"order_id\": \"ABC123\", \"customer_name\": \"John\", \"issue_type\": \"delayed_delivery\"})",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["data_fields"]
                }
            }
        }
    ]
