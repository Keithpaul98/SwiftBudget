"""
Budget Service - Business logic for budget goal management.

Why BudgetService?
- Encapsulates budget goal operations
- Calculates spending vs budget
- Determines alert status
- Validates budget constraints
- Provides budget insights

Design Pattern: Service Layer Pattern
"""

from typing import List, Optional, Dict
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func
from app import db
from app.models.budget_goal import BudgetGoal
from app.models.category import Category
from app.models.transaction import Transaction


class BudgetService:
    """Service class for budget goal operations."""
    
    @staticmethod
    def create_budget_goal(
        user_id: int,
        category_id: int,
        amount: Decimal,
        period: str,
        alert_threshold: int = 80
    ) -> BudgetGoal:
        """
        Create a new budget goal.
        
        Validations:
        - Amount must be positive
        - Category must exist and belong to user
        - Period must be valid ('monthly', 'weekly', 'yearly')
        - Alert threshold must be 0-100
        - Only one budget per category per user
        
        Args:
            user_id: User ID
            category_id: Category ID
            amount: Budget amount (positive)
            period: 'monthly', 'weekly', or 'yearly'
            alert_threshold: Alert at X% of budget (0-100, default 80)
        
        Returns:
            Created BudgetGoal object
        
        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError('Budget amount must be positive')
        
        # Validate period
        if period not in ['monthly', 'weekly', 'yearly']:
            raise ValueError('Period must be "monthly", "weekly", or "yearly"')
        
        # Validate alert threshold
        if not 0 <= alert_threshold <= 100:
            raise ValueError('Alert threshold must be between 0 and 100')
        
        # Validate category ownership
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if not category:
            raise ValueError('Category not found or does not belong to user')
        
        # Check for existing budget goal
        existing = BudgetGoal.query.filter_by(
            user_id=user_id,
            category_id=category_id
        ).first()
        
        if existing:
            raise ValueError(f'Budget goal already exists for category "{category.name}"')
        
        # Create budget goal
        budget_goal = BudgetGoal(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            period=period,
            alert_threshold=alert_threshold
        )
        
        db.session.add(budget_goal)
        db.session.commit()
        
        return budget_goal
    
    @staticmethod
    def get_budget_goal_by_id(budget_id: int, user_id: int) -> Optional[BudgetGoal]:
        """
        Get a budget goal by ID (with user ownership check).
        
        Args:
            budget_id: Budget goal ID
            user_id: User ID (for ownership verification)
        
        Returns:
            BudgetGoal object or None
        """
        return BudgetGoal.query.filter_by(id=budget_id, user_id=user_id).first()
    
    @staticmethod
    def get_user_budget_goals(user_id: int, active_only: bool = True) -> List[BudgetGoal]:
        """
        Get all budget goals for a user.
        
        Args:
            user_id: User ID
            active_only: Only return active budget goals (default True)
        
        Returns:
            List of BudgetGoal objects
        """
        query = BudgetGoal.query.filter_by(user_id=user_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(BudgetGoal.created_at.desc()).all()
    
    @staticmethod
    def update_budget_goal(
        budget_id: int,
        user_id: int,
        amount: Optional[Decimal] = None,
        period: Optional[str] = None,
        alert_threshold: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> BudgetGoal:
        """
        Update a budget goal.
        
        Args:
            budget_id: Budget goal ID
            user_id: User ID (for ownership verification)
            amount: New budget amount (optional)
            period: New period (optional)
            alert_threshold: New alert threshold (optional)
            is_active: New active status (optional)
        
        Returns:
            Updated BudgetGoal object
        
        Raises:
            ValueError: If validation fails or budget not found
        """
        budget_goal = BudgetService.get_budget_goal_by_id(budget_id, user_id)
        
        if not budget_goal:
            raise ValueError('Budget goal not found')
        
        # Update fields if provided
        if amount is not None:
            if amount <= 0:
                raise ValueError('Budget amount must be positive')
            budget_goal.amount = amount
        
        if period is not None:
            if period not in ['monthly', 'weekly', 'yearly']:
                raise ValueError('Period must be "monthly", "weekly", or "yearly"')
            budget_goal.period = period
        
        if alert_threshold is not None:
            if not 0 <= alert_threshold <= 100:
                raise ValueError('Alert threshold must be between 0 and 100')
            budget_goal.alert_threshold = alert_threshold
        
        if is_active is not None:
            budget_goal.is_active = is_active
        
        db.session.commit()
        
        return budget_goal
    
    @staticmethod
    def delete_budget_goal(budget_id: int, user_id: int) -> None:
        """
        Delete a budget goal.
        
        Why hard delete?
        - Budget goals are user preferences, not financial data
        - No need to preserve deleted budgets
        - Simplifies queries (no is_deleted flag needed)
        
        Args:
            budget_id: Budget goal ID
            user_id: User ID (for ownership verification)
        
        Raises:
            ValueError: If budget not found
        """
        budget_goal = BudgetService.get_budget_goal_by_id(budget_id, user_id)
        
        if not budget_goal:
            raise ValueError('Budget goal not found')
        
        db.session.delete(budget_goal)
        db.session.commit()
    
    @staticmethod
    def get_budget_status(budget_id: int, user_id: int) -> Dict:
        """
        Get current status of a budget goal.
        
        Why status?
        - Dashboard: Show budget progress
        - Alerts: Determine if user should be notified
        - Insights: Help user understand spending
        
        Args:
            budget_id: Budget goal ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Dictionary with budget status:
            {
                'budget_amount': Decimal,
                'current_spending': Decimal,
                'remaining': Decimal,
                'percentage_used': float,
                'is_over_budget': bool,
                'should_alert': bool,
                'alert_threshold': int,
                'period': str,
                'category_name': str
            }
        
        Raises:
            ValueError: If budget not found
        """
        budget_goal = BudgetService.get_budget_goal_by_id(budget_id, user_id)
        
        if not budget_goal:
            raise ValueError('Budget goal not found')
        
        # Get current spending
        current_spending = budget_goal.get_current_period_spending()
        remaining = budget_goal.get_remaining_budget()
        percentage_used = budget_goal.get_percentage_used()
        is_over_budget = budget_goal.is_over_budget()
        should_alert = budget_goal.should_alert()
        
        return {
            'budget_amount': float(budget_goal.amount),
            'current_spending': float(current_spending),
            'remaining': float(remaining),
            'percentage_used': percentage_used,
            'is_over_budget': is_over_budget,
            'should_alert': should_alert,
            'alert_threshold': budget_goal.alert_threshold,
            'period': budget_goal.period,
            'category_name': budget_goal.category.name,
            'is_active': budget_goal.is_active
        }
    
    @staticmethod
    def get_all_budget_statuses(user_id: int) -> List[Dict]:
        """
        Get status for all active budget goals.
        
        Why all statuses?
        - Dashboard overview: Show all budgets at once
        - Alert system: Check which budgets need alerts
        - Reports: Generate budget summary
        
        Args:
            user_id: User ID
        
        Returns:
            List of budget status dictionaries
        """
        budget_goals = BudgetService.get_user_budget_goals(user_id, active_only=True)
        
        statuses = []
        for budget in budget_goals:
            status = BudgetService.get_budget_status(budget.id, user_id)
            status['budget_id'] = budget.id
            statuses.append(status)
        
        return statuses
    
    @staticmethod
    def get_budgets_needing_alerts(user_id: int) -> List[BudgetGoal]:
        """
        Get budget goals that need alerts.
        
        Why separate method?
        - Email notifications: Send alerts for budgets over threshold
        - Dashboard badges: Show alert count
        - Background jobs: Periodic alert checks
        
        Args:
            user_id: User ID
        
        Returns:
            List of BudgetGoal objects that need alerts
        """
        budget_goals = BudgetService.get_user_budget_goals(user_id, active_only=True)
        
        return [budget for budget in budget_goals if budget.should_alert()]
    
    @staticmethod
    def toggle_budget_active(budget_id: int, user_id: int) -> BudgetGoal:
        """
        Toggle budget goal active status.
        
        Why toggle?
        - Temporary disable: User wants to pause budget tracking
        - Seasonal budgets: Enable/disable based on time of year
        - Flexibility: Don't force deletion
        
        Args:
            budget_id: Budget goal ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Updated BudgetGoal object
        
        Raises:
            ValueError: If budget not found
        """
        budget_goal = BudgetService.get_budget_goal_by_id(budget_id, user_id)
        
        if not budget_goal:
            raise ValueError('Budget goal not found')
        
        budget_goal.is_active = not budget_goal.is_active
        db.session.commit()
        
        return budget_goal
