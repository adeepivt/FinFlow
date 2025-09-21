import openai
from openai import OpenAI
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics

from app.config import settings
from app.models.transaction import Transaction

class InsightsService:
    def __init__(self):
        self.enabled = bool(settings.OPENAI_API_KEY)
        self.client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/",api_key=settings.OPENAI_API_KEY)
    
    def generate_spending_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        try:
            insights_data = self._analyze_spending_patterns(user_id, db)
            
            ai_insights = self._generate_ai_insights(insights_data) if self.enabled else []
            
            return {
                "summary": insights_data["summary"],
                "trends": insights_data["trends"],
                "anomalies": insights_data["anomalies"],
                "categories": insights_data["category_analysis"],
                "ai_insights": ai_insights,
                "recommendations": self._generate_recommendations(insights_data)
            }
            
        except Exception as e:
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    def _analyze_spending_patterns(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Analyze spending patterns and detect trends."""
        
        ninety_days_ago = datetime.now() - timedelta(days=90)
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= ninety_days_ago
        ).all()
        
        expenses = [t for t in transactions if t.amount < 0]
        income = [t for t in transactions if t.amount > 0]
        
        category_spending = defaultdict(list)
        for expense in expenses:
            category = expense.category or "uncategorized"
            category_spending[category].append(abs(float(expense.amount)))
        
        category_totals = {
            cat: sum(amounts) for cat, amounts in category_spending.items()
        }
        
        monthly_spending = self._analyze_monthly_trends(expenses)
        weekly_patterns = self._analyze_weekly_patterns(expenses)
        
        anomalies = self._detect_spending_anomalies(expenses)
        
        return {
            "summary": {
                "total_expenses": sum(abs(float(t.amount)) for t in expenses),
                "total_income": sum(float(t.amount) for t in income),
                "transaction_count": len(transactions),
                "average_transaction": statistics.mean([abs(float(t.amount)) for t in expenses]) if expenses else 0,
                "days_analyzed": 90
            },
            "category_analysis": category_totals,
            "trends": {
                "monthly": monthly_spending,
                "weekly": weekly_patterns
            },
            "anomalies": anomalies
        }
    
    def _analyze_monthly_trends(self, expenses: List[Transaction]) -> Dict[str, Any]:
        """Analyze month-over-month spending trends."""
        
        monthly_data = defaultdict(float)
        for expense in expenses:
            month_key = expense.transaction_date.strftime("%Y-%m")
            monthly_data[month_key] += abs(float(expense.amount))
        
        months = sorted(monthly_data.keys())
        if len(months) >= 2:
            current_month = monthly_data[months[-1]]
            previous_month = monthly_data[months[-2]]
            
            if previous_month > 0:
                trend_percentage = ((current_month - previous_month) / previous_month) * 100
            else:
                trend_percentage = 0
        else:
            trend_percentage = 0
        
        return {
            "monthly_totals": dict(monthly_data),
            "trend_percentage": round(trend_percentage, 1),
            "trend_direction": "up" if trend_percentage > 5 else "down" if trend_percentage < -5 else "stable"
        }
    
    def _analyze_weekly_patterns(self, expenses: List[Transaction]) -> Dict[str, Any]:
        daily_spending = defaultdict(list)
        for expense in expenses:
            day_name = expense.transaction_date.strftime("%A")
            daily_spending[day_name].append(abs(float(expense.amount)))
        
        daily_averages = {
            day: statistics.mean(amounts) if amounts else 0
            for day, amounts in daily_spending.items()
        }
        
        if daily_averages:
            highest_day = max(daily_averages, key=daily_averages.get)
            lowest_day = min(daily_averages, key=daily_averages.get)
        else:
            highest_day = lowest_day = None
        
        return {
            "daily_averages": daily_averages,
            "highest_spending_day": highest_day,
            "lowest_spending_day": lowest_day
        }
    
    def _detect_spending_anomalies(self, expenses: List[Transaction]) -> List[Dict[str, Any]]:
        if len(expenses) < 10:  # Need enough data for anomaly detection
            return []
        
        amounts = [abs(float(t.amount)) for t in expenses]
        mean_amount = statistics.mean(amounts)
        std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        threshold = mean_amount + (2 * std_amount)  # 2 standard deviations
        
        anomalies = []
        for expense in expenses:
            amount = abs(float(expense.amount))
            if amount > threshold and amount > 100:  # Only flag significant amounts
                anomalies.append({
                    "transaction_id": expense.id,
                    "description": expense.description,
                    "amount": amount,
                    "date": expense.transaction_date.strftime("%Y-%m-%d"),
                    "category": expense.category,
                    "deviation_factor": round(amount / mean_amount, 1)
                })
        
        return sorted(anomalies, key=lambda x: x["deviation_factor"], reverse=True)[:5]
    
    def _generate_ai_insights(self, data: Dict[str, Any]) -> List[str]:
        if not self.enabled:
            return []
        
        try:
            context = self._build_insights_context(data)
            
            prompt = f"""
Analyze this user's spending data and provide 3-5 key insights:

{context}

Generate insights that are:
1. Specific and actionable
2. Based on the data patterns
3. Helpful for financial improvement
4. Written in a friendly, conversational tone
5. Each insight should be 1-2 sentences

IMPORTANT: Return ONLY a valid JSON array of strings, nothing else. No explanations, no code blocks, no markdown formatting.

Example format:
["Your spending on restaurants increased by 30% this month - consider meal prepping to save money.", "You've been consistent with your savings goals, keep it up!"]

JSON Response:
"""
            
            
            # response = openai.ChatCompletion.create(
            #     model="gpt-3.5-turbo",
            #     messages=[
            #         {"role": "system", "content": "You are a financial advisor analyzing spending patterns."},
            #         {"role": "user", "content": prompt}
            #     ],
            #     max_tokens=300,
            #     temperature=0.7
            # )
            response2 = self.client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "You are a financial advisor analyzing spending patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
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
            

            import json
            insights_text = response2.choices[0].message.content.strip()
            print(insights_text, 'text\n\n',)
            # return [insights_text]
            try:
                insights = json.loads(insights_text)
                print(insights, 'loadesjs')
                return insights if isinstance(insights, list) else [insights_text]
            except json.JSONDecodeError:
                print('exept', insights_text)
                return [insights_text]
            
        except Exception as e:
            return [f"AI insights unavailable: {str(e)}"]
    
    def _build_insights_context(self, data: Dict[str, Any]) -> str:
        context_parts = []
        
        summary = data["summary"]
        context_parts.append(f"Total spending: ${summary['total_expenses']:.2f} over {summary['days_analyzed']} days")
        context_parts.append(f"Average transaction: ${summary['average_transaction']:.2f}")
        
        if data["category_analysis"]:
            top_categories = sorted(data["category_analysis"].items(), key=lambda x: x[1], reverse=True)[:3]
            category_text = ", ".join([f"{cat}: ${amt:.2f}" for cat, amt in top_categories])
            context_parts.append(f"Top spending categories: {category_text}")
        
        if data["trends"]["monthly"]["trend_percentage"]:
            trend = data["trends"]["monthly"]
            context_parts.append(f"Monthly trend: {trend['trend_direction']} by {abs(trend['trend_percentage']):.1f}%")
        
        if data["anomalies"]:
            context_parts.append(f"Found {len(data['anomalies'])} unusual transactions")
        
        return "\n".join(context_parts)
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate simple rule-based recommendations."""
        
        recommendations = []
        
        if data["category_analysis"]:
            top_category = max(data["category_analysis"].items(), key=lambda x: x[1])
            if top_category[1] > 500:  # If spending more than $500 in a category
                recommendations.append(f"Consider setting a budget for {top_category[0]} - it's your highest spending category at ${top_category[1]:.2f}")
        
        trend = data["trends"]["monthly"]
        if trend["trend_percentage"] > 20:
            recommendations.append("Your spending increased significantly this month. Review recent transactions to identify the cause.")
        elif trend["trend_percentage"] < -20:
            recommendations.append("Great job reducing your spending this month! Keep up the good work.")
        
        weekly = data["trends"]["weekly"]
        if weekly["highest_spending_day"] and weekly["daily_averages"]:
            highest_day = weekly["highest_spending_day"]
            avg_amount = weekly["daily_averages"][highest_day]
            if avg_amount > 100:
                recommendations.append(f"You tend to spend more on {highest_day}s (${avg_amount:.2f} average). Plan ahead to control weekend/weekday spending.")
        
        return recommendations


insights_service = InsightsService()