"""
Transaction Routes - CRUD operations for transactions.

Why separate transactions blueprint?
- Organized routes: All transaction operations in one place
- URL prefix: /transactions
- Reusable across application
- Easy to add API endpoints later
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_required, current_user
from app import db
from app.models.transaction import Transaction
from app.forms.transaction import TransactionForm, TransactionFilterForm
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.utils.audit import audit_log
from decimal import Decimal
import bleach
import csv
import io

# Create blueprint
transactions_bp = Blueprint(
    'transactions',
    __name__,
    url_prefix='/transactions'
)


@transactions_bp.route('/')
@login_required
def index():
    """
    List all transactions with optional filters.
    
    Query Parameters:
    - category_id: Filter by category
    - transaction_type: Filter by type (income/expense)
    - start_date: Filter from date
    - end_date: Filter to date
    
    Returns:
        Rendered transaction list template
    """
    # Get filter parameters from query string
    category_id_str = request.args.get('category_id')
    category_id = int(category_id_str) if category_id_str and category_id_str != '' else None
    transaction_type = request.args.get('transaction_type')
    if transaction_type == '':
        transaction_type = None
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_query = request.args.get('q', '').strip()
    
    # Convert date strings to date objects
    from datetime import datetime
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get filtered transactions
    transactions = TransactionService.get_user_transactions(
        user_id=current_user.id,
        category_id=category_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    
    # Apply search filter on description and category name
    if search_query:
        q_lower = search_query.lower()
        transactions = [
            t for t in transactions
            if (t.description and q_lower in t.description.lower()) or
               (t.category and q_lower in t.category.name.lower())
        ]
    
    # Get user categories for filter form
    categories = CategoryService.get_user_categories(current_user.id)
    
    # Create filter form
    filter_form = TransactionFilterForm()
    filter_form.category_id.choices = [('', 'All Categories')] + [
        (c.id, c.name) for c in categories
    ]
    
    return render_template(
        'transactions/index.html',
        transactions=transactions,
        filter_form=filter_form,
        search_query=search_query,
        title='Transactions'
    )


@transactions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Create a new transaction.
    
    GET: Display transaction form
    POST: Process form and create transaction
    
    Returns:
        GET: Rendered create form
        POST: Redirect to transactions list on success
    """
    form = TransactionForm()
    
    # Populate category choices
    categories = CategoryService.get_user_categories(current_user.id)
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    # Populate project choices
    from app.services.project_service import ProjectService
    projects = ProjectService.get_user_projects(current_user.id)
    form.project_id.choices = [('', 'No Project')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        try:
            # Calculate amount if quantity and unit_price provided
            amount = Decimal(str(form.amount.data))
            quantity = form.quantity.data if form.quantity.data else 1
            unit_price = Decimal(str(form.unit_price.data)) if form.unit_price.data else None
            
            # If unit_price is provided, calculate total amount
            if unit_price:
                amount = Decimal(str(quantity)) * unit_price
            
            # Sanitize user input
            description = bleach.clean(form.description.data or '', tags=[], strip=True)
            
            # Create transaction using service
            transaction = TransactionService.create_transaction(
                user_id=current_user.id,
                amount=amount,
                category_id=form.category_id.data,
                transaction_type=form.transaction_type.data,
                transaction_date=form.transaction_date.data,
                description=description
            )
            
            # Update quantity, unit_price, and project if provided
            if quantity or unit_price or form.project_id.data:
                transaction.quantity = int(quantity) if quantity else 1
                transaction.unit_price = unit_price
                transaction.project_id = form.project_id.data if form.project_id.data else None
                db.session.commit()
            
            # Check budget alerts for expenses
            if form.transaction_type.data == 'expense':
                try:
                    from app.services.budget_service import BudgetService
                    from app.services.email_service import EmailService
                    
                    # Get budget for this category
                    budget_statuses = BudgetService.get_all_budget_statuses(current_user.id)
                    current_app.logger.info(f'Checking {len(budget_statuses)} budgets for alerts')
                    
                    for status in budget_statuses:
                        if status['category_id'] == form.category_id.data:
                            current_app.logger.info(f'Found budget for category {status["category_name"]}: {status["percentage_used"]}% used')
                            
                            # Send alert if over threshold or exceeded
                            if status['is_over_budget']:
                                current_app.logger.info(f'Budget exceeded! Sending alert to {current_user.email}')
                                result = EmailService.send_budget_exceeded_alert(current_user.email, status)
                                current_app.logger.info(f'Email sent: {result}')
                            elif status['should_alert']:
                                current_app.logger.info(f'Budget threshold reached! Sending alert to {current_user.email}')
                                result = EmailService.send_budget_alert(current_user.email, status)
                                current_app.logger.info(f'Email sent: {result}')
                            break
                except Exception as e:
                    current_app.logger.error(f'Failed to send budget alert: {e}')
                    import traceback
                    current_app.logger.error(traceback.format_exc())
            
            # Audit log
            audit_log('CREATE', 'Transaction', transaction.id, new_value={
                'amount': str(amount),
                'type': form.transaction_type.data,
                'category_id': form.category_id.data
            })
            db.session.commit()
            
            flash(f'{form.transaction_type.data.capitalize()} transaction created successfully!', 'success')
            return redirect(url_for('transactions.index'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the transaction.', 'danger')
            current_app.logger.error(f'Transaction creation failed: {e}', exc_info=True)
    
    return render_template(
        'transactions/create.html',
        form=form,
        title='New Transaction'
    )


@transactions_bp.route('/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(transaction_id):
    """
    Edit an existing transaction.
    
    Args:
        transaction_id: Transaction ID to edit
    
    Returns:
        GET: Rendered edit form
        POST: Redirect to transactions list on success
    """
    # Get transaction (with ownership check)
    transaction = TransactionService.get_transaction_by_id(transaction_id, current_user.id)
    
    if not transaction:
        flash('Transaction not found.', 'danger')
        return redirect(url_for('transactions.index'))
    
    form = TransactionForm()
    
    # Populate category choices
    categories = CategoryService.get_user_categories(current_user.id)
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        try:
            # Calculate amount if quantity and unit_price provided
            amount = Decimal(str(form.amount.data))
            quantity = form.quantity.data if form.quantity.data else 1
            unit_price = Decimal(str(form.unit_price.data)) if form.unit_price.data else None
            
            # If unit_price is provided, calculate total amount
            if unit_price:
                amount = Decimal(str(quantity)) * unit_price
            
            # Sanitize user input
            description = bleach.clean(form.description.data or '', tags=[], strip=True)
            
            # Capture old values for audit
            old_values = {
                'amount': str(transaction.amount),
                'type': transaction.transaction_type,
                'category_id': transaction.category_id,
                'description': transaction.description
            }
            
            # Update transaction using service
            updated_transaction = TransactionService.update_transaction(
                transaction_id=transaction_id,
                user_id=current_user.id,
                amount=amount,
                category_id=form.category_id.data,
                transaction_type=form.transaction_type.data,
                transaction_date=form.transaction_date.data,
                description=description
            )
            
            # Update quantity, unit_price, and project
            updated_transaction.quantity = int(quantity) if quantity else 1
            updated_transaction.unit_price = unit_price
            updated_transaction.project_id = form.project_id.data if form.project_id.data else None
            db.session.commit()
            
            # Audit log
            audit_log('UPDATE', 'Transaction', transaction_id, old_value=old_values, new_value={
                'amount': str(amount),
                'type': form.transaction_type.data,
                'category_id': form.category_id.data
            })
            db.session.commit()
            
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions.index'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the transaction.', 'danger')
            current_app.logger.error(f'Transaction update failed: {e}', exc_info=True)
    
    # Populate project choices
    from app.services.project_service import ProjectService
    projects = ProjectService.get_user_projects(current_user.id)
    form.project_id.choices = [('', 'No Project')] + [(p.id, p.name) for p in projects]
    
    # Pre-populate form with existing data (GET request)
    if request.method == 'GET':
        form.amount.data = transaction.amount
        form.quantity.data = transaction.quantity if transaction.quantity else 1
        form.unit_price.data = transaction.unit_price
        form.category_id.data = transaction.category_id
        form.transaction_type.data = transaction.transaction_type
        form.transaction_date.data = transaction.transaction_date
        form.description.data = transaction.description
        form.project_id.data = transaction.project_id if transaction.project_id else ''
    
    return render_template(
        'transactions/edit.html',
        form=form,
        transaction=transaction,
        title='Edit Transaction'
    )


@transactions_bp.route('/<int:transaction_id>/delete', methods=['POST'])
@login_required
def delete(transaction_id):
    """
    Delete a transaction (soft delete).
    
    Why POST only?
    - Prevents accidental deletion via GET request
    - CSRF protection via Flask-WTF
    - RESTful best practice
    
    Args:
        transaction_id: Transaction ID to delete
    
    Returns:
        Redirect to transactions list
    """
    try:
        # Audit log before delete
        audit_log('DELETE', 'Transaction', transaction_id)
        TransactionService.delete_transaction(transaction_id, current_user.id)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the transaction.', 'danger')
        current_app.logger.error(f'Transaction deletion failed: {e}', exc_info=True)
    
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/<int:transaction_id>')
@login_required
def view(transaction_id):
    """
    View transaction details.
    
    Args:
        transaction_id: Transaction ID to view
    
    Returns:
        Rendered transaction detail template
    """
    transaction = TransactionService.get_transaction_by_id(transaction_id, current_user.id)
    
    if not transaction:
        flash('Transaction not found.', 'danger')
        return redirect(url_for('transactions.index'))
    
    return render_template(
        'transactions/view.html',
        transaction=transaction,
        title='Transaction Details'
    )


@transactions_bp.route('/export/csv')
@login_required
def export_csv():
    """Export user transactions to CSV file."""
    from datetime import datetime
    
    # Get optional date filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    transactions = TransactionService.get_user_transactions(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Build CSV in memory with UTF-8 BOM for Excel compatibility
    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM so Excel recognises encoding and columns
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Category', 'Description', 'Amount', 'Project'])
    
    for t in transactions:
        writer.writerow([
            t.transaction_date.strftime('%m/%d/%Y') if t.transaction_date else '',
            t.transaction_type.capitalize() if t.transaction_type else '',
            t.category.name if t.category else '',
            t.description or '',
            float(t.amount),
            t.project.name if t.project else ''
        ])
    
    output.seek(0)
    
    filename = f'swiftbudget_transactions_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
