"""
Recurring Transaction Routes - CRUD operations for recurring transactions.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.forms.recurring_transaction import RecurringTransactionForm
from app.services.category_service import CategoryService
from app.utils.audit import audit_log
from decimal import Decimal
import bleach

recurring_bp = Blueprint('recurring', __name__, url_prefix='/recurring')


@recurring_bp.route('/')
@login_required
def index():
    """List all recurring transactions for the current user."""
    recurring = RecurringTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(RecurringTransaction.next_due_date.asc()).all()
    
    return render_template(
        'recurring/index.html',
        recurring=recurring,
        title='Recurring Transactions'
    )


@recurring_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new recurring transaction."""
    form = RecurringTransactionForm()
    
    categories = CategoryService.get_user_categories(current_user.id)
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    from app.services.project_service import ProjectService
    projects = ProjectService.get_user_projects(current_user.id)
    form.project_id.choices = [('', 'No Project')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        try:
            description = bleach.clean(form.description.data or '', tags=[], strip=True)
            
            recurring = RecurringTransaction(
                user_id=current_user.id,
                amount=Decimal(str(form.amount.data)),
                transaction_type=form.transaction_type.data,
                category_id=form.category_id.data,
                project_id=form.project_id.data if form.project_id.data else None,
                frequency=form.frequency.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                next_due_date=form.start_date.data,
                description=description,
                is_active=True
            )
            
            db.session.add(recurring)
            db.session.commit()
            
            audit_log('CREATE', 'RecurringTransaction', recurring.id, new_value={
                'amount': str(recurring.amount),
                'frequency': recurring.frequency,
                'type': recurring.transaction_type
            })
            db.session.commit()
            
            flash('Recurring transaction created successfully!', 'success')
            return redirect(url_for('recurring.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the recurring transaction.', 'danger')
            current_app.logger.error(f'Recurring transaction creation failed: {e}', exc_info=True)
    
    return render_template(
        'recurring/create.html',
        form=form,
        title='New Recurring Transaction'
    )


@recurring_bp.route('/<int:recurring_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(recurring_id):
    """Edit an existing recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first()
    
    if not recurring:
        flash('Recurring transaction not found.', 'danger')
        return redirect(url_for('recurring.index'))
    
    form = RecurringTransactionForm()
    
    categories = CategoryService.get_user_categories(current_user.id)
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    from app.services.project_service import ProjectService
    projects = ProjectService.get_user_projects(current_user.id)
    form.project_id.choices = [('', 'No Project')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        try:
            description = bleach.clean(form.description.data or '', tags=[], strip=True)
            
            recurring.amount = Decimal(str(form.amount.data))
            recurring.transaction_type = form.transaction_type.data
            recurring.category_id = form.category_id.data
            recurring.project_id = form.project_id.data if form.project_id.data else None
            recurring.frequency = form.frequency.data
            recurring.start_date = form.start_date.data
            recurring.end_date = form.end_date.data
            recurring.description = description
            recurring.is_active = form.is_active.data
            
            db.session.commit()
            
            audit_log('UPDATE', 'RecurringTransaction', recurring.id)
            db.session.commit()
            
            flash('Recurring transaction updated successfully!', 'success')
            return redirect(url_for('recurring.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the recurring transaction.', 'danger')
            current_app.logger.error(f'Recurring transaction update failed: {e}', exc_info=True)
    
    if request.method == 'GET':
        form.amount.data = recurring.amount
        form.transaction_type.data = recurring.transaction_type
        form.category_id.data = recurring.category_id
        form.project_id.data = recurring.project_id or ''
        form.frequency.data = recurring.frequency
        form.start_date.data = recurring.start_date
        form.end_date.data = recurring.end_date
        form.description.data = recurring.description
        form.is_active.data = recurring.is_active
    
    return render_template(
        'recurring/edit.html',
        form=form,
        recurring=recurring,
        title='Edit Recurring Transaction'
    )


@recurring_bp.route('/<int:recurring_id>/delete', methods=['POST'])
@login_required
def delete(recurring_id):
    """Delete a recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first()
    
    if not recurring:
        flash('Recurring transaction not found.', 'danger')
    else:
        try:
            audit_log('DELETE', 'RecurringTransaction', recurring.id)
            db.session.delete(recurring)
            db.session.commit()
            flash('Recurring transaction deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while deleting the recurring transaction.', 'danger')
            current_app.logger.error(f'Recurring transaction deletion failed: {e}', exc_info=True)
    
    return redirect(url_for('recurring.index'))


@recurring_bp.route('/<int:recurring_id>/toggle', methods=['POST'])
@login_required
def toggle(recurring_id):
    """Toggle active status of a recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first()
    
    if not recurring:
        flash('Recurring transaction not found.', 'danger')
    else:
        recurring.is_active = not recurring.is_active
        db.session.commit()
        status = 'activated' if recurring.is_active else 'paused'
        flash(f'Recurring transaction {status}.', 'success')
    
    return redirect(url_for('recurring.index'))


@recurring_bp.route('/process', methods=['POST'])
@login_required
def process_due():
    """Process all due recurring transactions for the current user."""
    due_items = RecurringTransaction.query.filter(
        RecurringTransaction.user_id == current_user.id,
        RecurringTransaction.is_active == True,
        RecurringTransaction.next_due_date <= db.func.current_date()
    ).all()
    
    created_count = 0
    for item in due_items:
        # Check end date
        if item.end_date and item.next_due_date > item.end_date:
            item.is_active = False
            continue
        
        try:
            transaction = Transaction(
                user_id=current_user.id,
                amount=item.amount,
                category_id=item.category_id,
                project_id=item.project_id,
                transaction_type=item.transaction_type,
                transaction_date=item.next_due_date,
                description=f"[Auto] {item.description or ''}"
            )
            db.session.add(transaction)
            
            item.last_created_date = item.next_due_date
            item.next_due_date = item.calculate_next_due()
            created_count += 1
            
        except Exception as e:
            current_app.logger.error(f'Failed to process recurring transaction {item.id}: {e}')
    
    db.session.commit()
    
    if created_count > 0:
        flash(f'{created_count} recurring transaction(s) processed!', 'success')
    else:
        flash('No recurring transactions were due.', 'info')
    
    return redirect(url_for('recurring.index'))
