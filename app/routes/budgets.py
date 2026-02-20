"""
Budget Goal Routes - CRUD operations for budget goals.

Why separate budgets blueprint?
- Organized routes: All budget operations in one place
- URL prefix: /budgets
- Reusable across application
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.forms.budget import BudgetGoalForm
from app.services.budget_service import BudgetService
from app.services.category_service import CategoryService
from decimal import Decimal

# Create blueprint
budgets_bp = Blueprint(
    'budgets',
    __name__,
    url_prefix='/budgets'
)


@budgets_bp.route('/')
@login_required
def index():
    """
    List all budget goals with current status.
    
    Shows:
    - All active budget goals
    - Current spending vs budget
    - Alert status
    - Progress bars
    
    Returns:
        Rendered budget list template
    """
    # Get all budget statuses
    budget_statuses = BudgetService.get_all_budget_statuses(current_user.id)
    
    # Get budgets needing alerts
    alert_budgets = BudgetService.get_budgets_needing_alerts(current_user.id)
    
    return render_template(
        'budgets/index.html',
        budget_statuses=budget_statuses,
        alert_budgets=alert_budgets,
        title='Budget Goals'
    )


@budgets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Create a new budget goal.
    
    GET: Display budget form
    POST: Process form and create budget
    
    Returns:
        GET: Rendered create form
        POST: Redirect to budgets list on success
    """
    form = BudgetGoalForm()
    
    # Populate category choices with all categories
    all_categories = CategoryService.get_user_categories(current_user.id)
    form.category_id.choices = [(c.id, c.name) for c in all_categories]
    
    if not all_categories:
        flash('Please create at least one category first.', 'warning')
        return redirect(url_for('budgets.index'))
    
    if form.validate_on_submit():
        try:
            # Create budget goal using service
            budget_goal = BudgetService.create_budget_goal(
                user_id=current_user.id,
                category_id=form.category_id.data,
                amount=Decimal(str(form.amount.data)),
                period=form.period.data,
                alert_threshold=form.alert_threshold.data
            )
            
            # Set active status
            budget_goal.is_active = form.is_active.data
            db.session.commit()
            
            # Refresh to load relationships
            db.session.refresh(budget_goal)
            
            flash(f'Budget goal for {budget_goal.category.name} created successfully!', 'success')
            return redirect(url_for('budgets.index'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the budget goal.', 'danger')
            print(f"Budget creation error: {e}")
    
    return render_template(
        'budgets/create.html',
        form=form,
        title='New Budget Goal'
    )


@budgets_bp.route('/<int:budget_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(budget_id):
    """
    Edit an existing budget goal.
    
    Args:
        budget_id: Budget goal ID to edit
    
    Returns:
        GET: Rendered edit form
        POST: Redirect to budgets list on success
    """
    # Get budget goal (with ownership check)
    budget_goal = BudgetService.get_budget_goal_by_id(budget_id, current_user.id)
    
    if not budget_goal:
        flash('Budget goal not found.', 'danger')
        return redirect(url_for('budgets.index'))
    
    form = BudgetGoalForm()
    
    # Category is fixed (can't change category of existing budget)
    # Must set choices before validation
    form.category_id.choices = [(budget_goal.category_id, budget_goal.category.name)]
    form.category_id.data = budget_goal.category_id
    
    if form.validate_on_submit():
        try:
            # Update budget goal using service
            BudgetService.update_budget_goal(
                budget_id=budget_id,
                user_id=current_user.id,
                amount=Decimal(str(form.amount.data)),
                period=form.period.data,
                alert_threshold=form.alert_threshold.data,
                is_active=form.is_active.data
            )
            
            flash('Budget goal updated successfully!', 'success')
            return redirect(url_for('budgets.index'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the budget goal.', 'danger')
            print(f"Budget update error: {e}")
    elif request.method == 'POST':
        # Form validation failed
        print(f"Form validation errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    # Pre-populate form with existing data (GET request)
    if request.method == 'GET':
        form.category_id.data = budget_goal.category_id
        form.amount.data = budget_goal.amount
        form.period.data = budget_goal.period
        form.alert_threshold.data = budget_goal.alert_threshold
        form.is_active.data = budget_goal.is_active
    
    return render_template(
        'budgets/edit.html',
        form=form,
        budget_goal=budget_goal,
        title='Edit Budget Goal'
    )


@budgets_bp.route('/<int:budget_id>/delete', methods=['POST'])
@login_required
def delete(budget_id):
    """
    Delete a budget goal.
    
    Why POST only?
    - Prevents accidental deletion via GET request
    - CSRF protection via Flask-WTF
    - RESTful best practice
    
    Args:
        budget_id: Budget goal ID to delete
    
    Returns:
        Redirect to budgets list
    """
    try:
        BudgetService.delete_budget_goal(budget_id, current_user.id)
        flash('Budget goal deleted successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the budget goal.', 'danger')
        print(f"Budget deletion error: {e}")
    
    return redirect(url_for('budgets.index'))


@budgets_bp.route('/<int:budget_id>/toggle', methods=['POST'])
@login_required
def toggle_active(budget_id):
    """
    Toggle budget goal active status.
    
    Why toggle?
    - Quick enable/disable without editing
    - Seasonal budgets
    - Temporary pause
    
    Args:
        budget_id: Budget goal ID to toggle
    
    Returns:
        Redirect to budgets list
    """
    try:
        budget_goal = BudgetService.toggle_budget_active(budget_id, current_user.id)
        status = 'activated' if budget_goal.is_active else 'deactivated'
        flash(f'Budget goal {status} successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while toggling the budget goal.', 'danger')
        print(f"Budget toggle error: {e}")
    
    return redirect(url_for('budgets.index'))
