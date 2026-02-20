"""
Project Forms - Create and Edit Projects.

Why separate project forms?
- Project name validation
- Color picker support
- Active/archived status
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ProjectForm(FlaskForm):
    """
    Form for creating/editing projects.
    
    Fields:
    - name: Project name (required)
    - description: Optional description
    - color: Hex color code for visual distinction
    - is_active: Whether project is active
    """
    
    name = StringField(
        'Project Name',
        validators=[
            DataRequired(message='Project name is required'),
            Length(min=1, max=100, message='Project name must be between 1 and 100 characters')
        ],
        render_kw={
            'placeholder': 'e.g., Parents Shopping - Feb 2026',
            'class': 'form-control'
        }
    )
    # Why name validation?
    # - Required field
    # - Max 100 characters (database constraint)
    # - Unique per user (checked in service layer)
    
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500, message='Description must be 500 characters or less')],
        render_kw={
            'placeholder': 'Optional: Add details about this project',
            'class': 'form-control',
            'rows': 3
        }
    )
    # Why optional?
    # - Not all projects need detailed descriptions
    # - Name is often self-explanatory
    
    color = StringField(
        'Color',
        validators=[Optional()],
        default='#6c757d',
        render_kw={
            'type': 'color',
            'class': 'form-control form-control-color',
            'title': 'Choose a color for this project'
        }
    )
    # Why color picker?
    # - Visual distinction in UI
    # - Easy to identify projects at a glance
    # - HTML5 color input type
    
    is_active = BooleanField(
        'Active',
        default=True,
        render_kw={'class': 'form-check-input'}
    )
    # Why is_active?
    # - Archive completed projects
    # - Don't delete (preserve history)
    # - Can reactivate if needed
    
    submit = SubmitField(
        'Save Project',
        render_kw={'class': 'btn btn-primary'}
    )
