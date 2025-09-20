from openai import OpenAI
# from google import genai
from typing import Optional
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

STANDARD_CATEGORIES = [
    "food_dining",     
    "groceries",       
    "transportation",  
    "utilities",       
    "housing",         
    "healthcare",      
    "entertainment",   
    "shopping",       
    "education",       
    "travel",          
    "income",          
    "transfer",        
    "other"             
]

class CategorizationService:
    """AI service for transaction categorization."""

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/",api_key=settings.OPENAI_API_KEY)
            # self.client = genai.Client(api_key=settings.OPENAI_API_KEY)
            self.enabled = True
        else:
            self.client = None 
            self.enabled = False
            logger.warning("OpenAI API key not configured. AI categorization disabled.")
    
    def categorize_transaction(self, description: str, amount: float, merchant: Optional[str] = None) -> str:
        """
        Categorize a transaction using AI.
        
        Args:
            description: Transaction description
            amount: Transaction amount (positive/negative)
            merchant: Optional merchant name
            
        Returns:
            Category string from STANDARD_CATEGORIES
        """
 
        if not self.enabled:
            return "other"
        
        try:
            prompt = self._build_categorization_prompt(description, amount, merchant)
            
            # response = self.client.chat.completions.create(
            #             model="gpt-3.5-turbo",
            #             messages=[
            #                 {"role": "system", "content": "You are a financial transaction categorization expert."},
            #                 {"role": "user", "content": prompt}
            #             ],
            #             max_tokens=50,
            #             temperature=0.1
            #         )
            response = self.client.chat.completions.create(
                model="gemini-2.5-flash",
                # reasoning_effort="low",
                messages=[
                    {"role": "system", "content": "You are a financial transaction categorization expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1,
                extra_body={
                    'extra_body': {
                        "google": {
                        "thinking_config": {
                            "thinking_budget": 0,
                            "include_thoughts": False
                        }
                        }
                    }
                    }
            )
            print(response.choices[0].message.content.strip().lower())
            # response = self.client.models.generate_content(
            #             model="gemini-2.5-flash", 
            #             contents=prompt,
            #         )

            # print(response, '-----', response.text.strip().lower())
            category = response.choices[0].message.content.strip().lower()
            
            if category in STANDARD_CATEGORIES:
                logger.info(f"AI categorized '{description}' as '{category}'")
                return category
            else:
                logger.warning(f"AI returned invalid category '{category}' for '{description}'")
                return "other"
                
        except Exception as e:
            logger.error(f"AI categorization failed for '{description}': {str(e)}")
            return self._fallback_categorization(description, amount)
    
    def _build_categorization_prompt(self, description: str, amount: float, merchant: Optional[str] = None) -> str:
        """Build prompt for OpenAI categorization."""
        
        transaction_type = "income" if amount > 0 else "expense"
        merchant_info = f" at {merchant}" if merchant else ""
        
        prompt = f"""
                Categorize this financial transaction into ONE of these exact categories:
                {', '.join(STANDARD_CATEGORIES)}

                Transaction details:
                - Description: "{description}"
                - Amount: ₹{abs(amount):.2f} ({transaction_type})
                {f"- Merchant: {merchant}" if merchant else ""}

                Rules:
                1. Return ONLY the category name, nothing else
                2. Use lowercase with underscores (e.g., "food_dining")
                3. Choose the most specific category that applies
                4. If unsure, use "other"

                Examples:
                - "McDonald's" → food_dining
                - "Walmart Grocery" → groceries
                - "Shell Gas Station" → transportation
                - "Netflix Subscription" → entertainment
                - "Salary Deposit" → income

                Category:"""

        return prompt
    
    def _fallback_categorization(self, description: str, amount: float) -> str:
        """
        Fallback categorization using simple keyword matching.
        Used when AI fails or is disabled.
        """
        description_lower = description.lower()
        
        if amount > 0:
            return "income"
        
        food_keywords = ["restaurant", "mcdonald", "burger", "pizza", "cafe", "coffee", "dining"]
        grocery_keywords = ["grocery", "supermarket", "walmart", "target", "costco", "market"]
        gas_keywords = ["gas", "shell", "exxon", "bp", "chevron", "fuel"]
        
        for keyword in food_keywords:
            if keyword in description_lower:
                return "food_dining"
        
        for keyword in grocery_keywords:
            if keyword in description_lower:
                return "groceries"
                
        for keyword in gas_keywords:
            if keyword in description_lower:
                return "transportation"
        
        return "other"
    
    def batch_categorize_transactions(self, transactions: list) -> dict:
        """
        Categorize multiple transactions at once.
        More efficient for bulk operations.
        
        Args:
            transactions: List of dicts with 'id', 'description', 'amount'
            
        Returns:
            Dict mapping transaction_id to category
        """
        results = {}
        
        for transaction in transactions:
            category = self.categorize_transaction(
                transaction['description'],
                transaction['amount'],
                transaction.get('merchant')
            )
            results[transaction['id']] = category
        
        return results


categorization_service = CategorizationService()