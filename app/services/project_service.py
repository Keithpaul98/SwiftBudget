"""
Project Service - Business logic for project management.

Why ProjectService?
- Encapsulates project operations
- Validates project data
- Provides project statistics
- Manages project lifecycle
"""

from typing import List, Optional, Dict
from app import db
from app.models.project import Project
from app.models.transaction import Transaction


class ProjectService:
    """Service class for project operations."""
    
    @staticmethod
    def create_project(
        user_id: int,
        name: str,
        description: str = None,
        color: str = '#6c757d'
    ) -> Project:
        """
        Create a new project.
        
        Args:
            user_id: User ID
            name: Project name
            description: Optional project description
            color: Hex color code (default: gray)
        
        Returns:
            Created Project object
        
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError('Project name is required')
        
        name = name.strip()
        
        if len(name) > 100:
            raise ValueError('Project name must be 100 characters or less')
        
        # Check for duplicate project name
        existing = Project.query.filter_by(
            user_id=user_id,
            name=name
        ).first()
        
        if existing:
            raise ValueError(f'Project "{name}" already exists')
        
        # Validate color (basic hex validation)
        if color and not color.startswith('#'):
            color = f'#{color}'
        
        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            color=color
        )
        
        db.session.add(project)
        db.session.commit()
        
        return project
    
    @staticmethod
    def get_user_projects(
        user_id: int,
        active_only: bool = True
    ) -> List[Project]:
        """
        Get all projects for a user.
        
        Args:
            user_id: User ID
            active_only: Only return active projects (default: True)
        
        Returns:
            List of Project objects
        """
        query = Project.query.filter_by(user_id=user_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(Project.name).all()
    
    @staticmethod
    def get_project_by_id(project_id: int, user_id: int) -> Optional[Project]:
        """
        Get a project by ID (with ownership check).
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Project object or None
        """
        return Project.query.filter_by(
            id=project_id,
            user_id=user_id
        ).first()
    
    @staticmethod
    def update_project(
        project_id: int,
        user_id: int,
        name: str = None,
        description: str = None,
        color: str = None,
        is_active: bool = None
    ) -> Project:
        """
        Update a project.
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            name: New project name (optional)
            description: New description (optional)
            color: New color (optional)
            is_active: New active status (optional)
        
        Returns:
            Updated Project object
        
        Raises:
            ValueError: If project not found or validation fails
        """
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            raise ValueError('Project not found')
        
        # Update name if provided
        if name is not None:
            name = name.strip()
            
            if not name:
                raise ValueError('Project name cannot be empty')
            
            if len(name) > 100:
                raise ValueError('Project name must be 100 characters or less')
            
            # Check for duplicate name (excluding current project)
            existing = Project.query.filter(
                Project.user_id == user_id,
                Project.name == name,
                Project.id != project_id
            ).first()
            
            if existing:
                raise ValueError(f'Project "{name}" already exists')
            
            project.name = name
        
        # Update other fields
        if description is not None:
            project.description = description
        
        if color is not None:
            if color and not color.startswith('#'):
                color = f'#{color}'
            project.color = color
        
        if is_active is not None:
            project.is_active = is_active
        
        db.session.commit()
        
        return project
    
    @staticmethod
    def delete_project(project_id: int, user_id: int) -> None:
        """
        Delete a project.
        
        Note: Transactions linked to this project will have project_id set to NULL.
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
        
        Raises:
            ValueError: If project not found
        """
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            raise ValueError('Project not found')
        
        db.session.delete(project)
        db.session.commit()
    
    @staticmethod
    def toggle_project_active(project_id: int, user_id: int) -> Project:
        """
        Toggle project active status.
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Updated Project object
        
        Raises:
            ValueError: If project not found
        """
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            raise ValueError('Project not found')
        
        project.is_active = not project.is_active
        db.session.commit()
        
        return project
    
    @staticmethod
    def get_project_statistics(project_id: int, user_id: int) -> Dict:
        """
        Get statistics for a project.
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
        
        Returns:
            dict: Project statistics
        
        Raises:
            ValueError: If project not found
        """
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            raise ValueError('Project not found')
        
        summary = project.get_transaction_summary()
        
        return {
            'project_id': project.id,
            'project_name': project.name,
            'is_active': project.is_active,
            'total_income': summary['total_income'],
            'total_expenses': summary['total_expenses'],
            'net_spending': summary['net_spending'],
            'transaction_count': summary['transaction_count'],
            'created_at': project.created_at.isoformat() if project.created_at else None
        }
    
    @staticmethod
    def get_all_project_statistics(user_id: int) -> List[Dict]:
        """
        Get statistics for all user projects.
        
        Args:
            user_id: User ID
        
        Returns:
            List of project statistics
        """
        projects = ProjectService.get_user_projects(user_id, active_only=False)
        
        return [
            ProjectService.get_project_statistics(project.id, user_id)
            for project in projects
        ]
