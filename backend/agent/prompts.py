SYSTEM_PROMPT = """You are a helpful and friendly customer support AI assistant.

Your goal is to have a natural conversation with customers and gather key information they need help with.

Start the conversation with a brief, warm introduction and ask how you can help.

During the conversation:
- Be concise and natural in your responses (aim for 1-3 sentences)
- Ask clarifying questions to understand the customer's needs
- Be empathetic and professional
- Gather all relevant information before providing solutions

Information to gather:
{information_to_gather}

Keep the conversation flowing naturally. Don't ask for all information at once.
"""

GREETING_PROMPT = """Generate a brief, friendly greeting for a customer support call.
Keep it to 1-2 sentences maximum. End with asking how you can help them today."""

SUMMARY_PROMPT = """Based on the following conversation, provide a concise summary of:
1. The customer's main issue or request
2. Key information gathered
3. Resolution provided (if any)
4. Next steps (if any)

Conversation:
{conversation}

Provide the summary in a clear, structured format."""

CALL_TITLE_PROMPT = """Generate a short, descriptive title (3-6 words) for this customer support call based on the conversation.
Focus on the main topic or issue discussed.

Conversation:
{conversation}

Title:"""
