"""
Category Service - Business logic for category management.

Why CategoryService?
- Encapsulates category-related operations
- Handles default category creation
- Validates category operations
- Prevents deletion of categories with transactions
- Reusable across routes and background jobs

Design Pattern: Service Layer Pattern
- Routes call services, not models directly
- Services handle business logic and validation
- Models handle data persistence only
"""

from typing import List, Optional
from app import db
from app.models.category import Category
from app.models.transaction import Transaction


class CategoryService:
    """Service class for category operations."""
    
    @staticmethod
    def get_user_categories(user_id: int) -> List[Category]:
        """
        Get all categories for a user.
        
        Why static method?
        - No instance state needed
        - Can be called without creating CategoryService object
        - Cleaner syntax: CategoryService.get_user_categories(user_id)
        
        Args:
            user_id: User ID
        
        Returns:
            List of Category objects
        """
        return Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
    
    @staticmethod
    def get_category_by_id(category_id: int, user_id: int) -> Optional[Category]:
        """
        Get a specific category by ID (with user ownership check).
        
        Why check user_id?
        - Security: Prevent users from accessing other users' categories
        - Authorization: Ensure user owns the category
        
        Args:
            category_id: Category ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Category object or None if not found or not owned by user
        """
        return Category.query.filter_by(id=category_id, user_id=user_id).first()
    
    @staticmethod
    def create_category(name: str, user_id: int, is_default: bool = False) -> Category:
        """
        Create a new category.
        
        Why validate name?
        - Prevent duplicate category names per user
        - Unique constraint: (user_id, name)
        
        Args:
            name: Category name
            user_id: User ID
            is_default: Whether this is a system default category
        
        Returns:
            Created Category object
        
        Raises:
            ValueError: If category name already exists for user
        """
        # Check if category already exists
        existing = Category.query.filter_by(user_id=user_id, name=name).first()
        if existing:
            raise ValueError(f'Category "{name}" already exists')
        
        # Create category
        category = Category(
            name=name,
            user_id=user_id,
            is_default=is_default
        )
        
        db.session.add(category)
        db.session.commit()
        
        return category
    
    @staticmethod
    def update_category(category_id: int, user_id: int, name: str) -> Category:
        """
        Update category name.
        
        Why prevent default category updates?
        - System categories should remain consistent
        - Prevents confusion (e.g., renaming "Food" to "Groceries")
        
        Args:
            category_id: Category ID
            user_id: User ID (for ownership verification)
            name: New category name
        
        Returns:
            Updated Category object
        
        Raises:
            ValueError: If category not found, not owned, is default, or name exists
        """
        category = CategoryService.get_category_by_id(category_id, user_id)
        
        if not category:
            raise ValueError('Category not found')
        
        if category.is_default:
            raise ValueError('Cannot modify default categories')
        
        # Check if new name already exists (excluding current category)
        existing = Category.query.filter(
            Category.user_id == user_id,
            Category.name == name,
            Category.id != category_id
        ).first()
        
        if existing:
            raise ValueError(f'Category "{name}" already exists')
        
        category.name = name
        db.session.commit()
        
        return category
    
    @staticmethod
    def delete_category(category_id: int, user_id: int) -> None:
        """
        Delete a category.
        
        Why prevent deletion?
        - Default categories: System categories should not be deleted
        - Categories with transactions: Prevents orphaned transactions
        
        Database constraint: ON DELETE RESTRICT for transactions
        - Prevents deletion if category has transactions
        - Raises IntegrityError if attempted
        
        Args:
            category_id: Category ID
            user_id: User ID (for ownership verification)
        
        Raises:
            ValueError: If category not found, not owned, is default, or has transactions
        """
        category = CategoryService.get_category_by_id(category_id, user_id)
        
        if not category:
            raise ValueError('Category not found')
        
        if category.is_default:
            raise ValueError('Cannot delete default categories')
        
        # Check if category has transactions
        transaction_count = Transaction.query.filter_by(category_id=category_id).count()
        if transaction_count > 0:
            raise ValueError(
                f'Cannot delete category with {transaction_count} transaction(s). '
                'Please reassign or delete transactions first.'
            )
        
        db.session.delete(category)
        db.session.commit()
    
    @staticmethod
    def create_default_categories(user_id: int) -> List[Category]:
        """
        Create default categories for a new user.
        
        Why default categories?
        - Better onboarding: User can start immediately
        - Common use cases: Most users need these categories
        - Consistency: All users have same starting point
        
        Default Categories:
        - Income: Salary, Freelance, Investments
        - Expenses: Food, Rent, Transportation, Utilities, Entertainment, Healthcare, Shopping, Other
        
        Args:
            user_id: User ID
        
        Returns:
            List of created Category objects
        """
        # Use the model's class method
        return Category.create_default_categories_for_user(user_id)
    
    @staticmethod
    def get_category_statistics(category_id: int, user_id: int) -> dict:
        """
        Get statistics for a category.
        
        Why statistics?
        - Show category usage
        - Help users understand spending patterns
        - Inform deletion decisions
        
        Args:
            category_id: Category ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Dictionary with category statistics:
            {
                'transaction_count': int,
                'total_spent': Decimal,
                'total_earned': Decimal,
                'has_budget_goal': bool
            }
        
        Raises:
            ValueError: If category not found or not owned by user
        """
        category = CategoryService.get_category_by_id(category_id, user_id)
        
        if not category:
            raise ValueError('Category not found')
        
        # Get transaction statistics
        from sqlalchemy import func
        from app.models.budget_goal import BudgetGoal
        
        # Count transactions
        transaction_count = Transaction.query.filter_by(
            category_id=category_id,
            is_deleted=False
        ).count()
        
        # Sum expenses
        total_spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == category_id,
            Transaction.transaction_type == 'expense',
            Transaction.is_deleted == False
        ).scalar() or 0
        
        # Sum income
        total_earned = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == category_id,
            Transaction.transaction_type == 'income',
            Transaction.is_deleted == False
        ).scalar() or 0
        
        # Check if category has budget goal
        has_budget_goal = BudgetGoal.query.filter_by(
            category_id=category_id,
            is_active=True
        ).first() is not None
        
        return {
            'transaction_count': transaction_count,
            'total_spent': float(total_spent),
            'total_earned': float(total_earned),
            'has_budget_goal': has_budget_goal
        }
