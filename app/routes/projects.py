"""
Project Routes - CRUD operations for projects.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.forms.project import ProjectForm
from app.services.project_service import ProjectService

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
@login_required
def index():
    """List all projects with statistics."""
    projects = ProjectService.get_all_project_statistics(current_user.id)
    return render_template('projects/index.html', projects=projects, title='Projects')


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project."""
    form = ProjectForm()
    
    if form.validate_on_submit():
        try:
            ProjectService.create_project(
                user_id=current_user.id,
                name=form.name.data,
                description=form.description.data,
                color=form.color.data
            )
            flash(f'Project "{form.name.data}" created successfully!', 'success')
            return redirect(url_for('projects.index'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('projects/create.html', form=form, title='New Project')


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    """Edit an existing project."""
    project = ProjectService.get_project_by_id(project_id, current_user.id)
    
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.index'))
    
    form = ProjectForm()
    
    if form.validate_on_submit():
        try:
            ProjectService.update_project(
                project_id=project_id,
                user_id=current_user.id,
                name=form.name.data,
                description=form.description.data,
                color=form.color.data,
                is_active=form.is_active.data
            )
            flash('Project updated successfully!', 'success')
            return redirect(url_for('projects.index'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    if request.method == 'GET':
        form.name.data = project.name
        form.description.data = project.description
        form.color.data = project.color
        form.is_active.data = project.is_active
    
    return render_template('projects/edit.html', form=form, project=project, title='Edit Project')


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    """Delete a project."""
    try:
        ProjectService.delete_project(project_id, current_user.id)
        flash('Project deleted successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('projects.index'))


@projects_bp.route('/<int:project_id>/toggle', methods=['POST'])
@login_required
def toggle_active(project_id):
    """Toggle project active status."""
    try:
        project = ProjectService.toggle_project_active(project_id, current_user.id)
        status = 'activated' if project.is_active else 'archived'
        flash(f'Project {status} successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('projects.index'))
