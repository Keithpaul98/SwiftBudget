"""
Email Service - Send notifications and alerts.

Why EmailService?
- Centralized email sending logic
- Budget alert notifications
- Spending summary emails
- Professional HTML email templates
"""

from flask import render_template, current_app
from flask_mail import Message
from app import mail
from typing import List, Dict
from datetime import datetime


class EmailService:
    """Service class for email operations."""
    
    @staticmethod
    def send_email(subject: str, recipients: List[str], text_body: str, html_body: str) -> bool:
        """
        Send an email.
        
        Args:
            subject: Email subject
            recipients: List of recipient email addresses
            text_body: Plain text email body
            html_body: HTML email body
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            msg.body = text_body
            msg.html = html_body
            
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {e}')
            return False
    
    @staticmethod
    def send_budget_alert(user_email: str, budget_data: Dict) -> bool:
        """
        Send budget alert notification.
        
        Args:
            user_email: User's email address
            budget_data: Dictionary containing budget information
                - category_name: str
                - budget_amount: float
                - current_spending: float
                - percentage_used: float
                - period: str
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"Budget Alert: {budget_data['category_name']}"
        
        text_body = render_template(
            'emails/budget_alert.txt',
            budget=budget_data
        )
        
        html_body = render_template(
            'emails/budget_alert.html',
            budget=budget_data
        )
        
        return EmailService.send_email(
            subject=subject,
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_budget_exceeded_alert(user_email: str, budget_data: Dict) -> bool:
        """
        Send budget exceeded notification.
        
        Args:
            user_email: User's email address
            budget_data: Dictionary containing budget information
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"⚠️ Budget Exceeded: {budget_data['category_name']}"
        
        text_body = render_template(
            'emails/budget_exceeded.txt',
            budget=budget_data
        )
        
        html_body = render_template(
            'emails/budget_exceeded.html',
            budget=budget_data
        )
        
        return EmailService.send_email(
            subject=subject,
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_weekly_summary(user_email: str, summary_data: Dict) -> bool:
        """
        Send weekly spending summary.
        
        Args:
            user_email: User's email address
            summary_data: Dictionary containing summary information
                - week_start: date
                - week_end: date
                - total_income: float
                - total_expenses: float
                - net_balance: float
                - top_categories: List[Dict]
                - budget_statuses: List[Dict]
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"Weekly Summary: {summary_data['week_start']} - {summary_data['week_end']}"
        
        text_body = render_template(
            'emails/weekly_summary.txt',
            summary=summary_data
        )
        
        html_body = render_template(
            'emails/weekly_summary.html',
            summary=summary_data
        )
        
        return EmailService.send_email(
            subject=subject,
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_welcome_email(user_email: str, username: str) -> bool:
        """
        Send welcome email to new users.
        
        Args:
            user_email: User's email address
            username: User's username
        
        Returns:
            bool: True if sent successfully
        """
        subject = "Welcome to SwiftBudget!"
        
        text_body = render_template(
            'emails/welcome.txt',
            username=username
        )
        
        html_body = render_template(
            'emails/welcome.html',
            username=username
        )
        
        return EmailService.send_email(
            subject=subject,
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
