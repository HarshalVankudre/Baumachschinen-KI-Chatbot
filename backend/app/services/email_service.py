"""
Email Service

Handles all email operations:
- Email verification
- Admin notifications
- User approval/rejection notifications
- Password reset (future)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Email templates directory
EMAIL_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "email_previews"


def load_email_template(template_name: str) -> str:
    """
    Load email template from file

    Args:
        template_name: Name of the template file (e.g., "01_verification_email.html")

    Returns:
        Template content as string
    """
    template_path = EMAIL_TEMPLATES_DIR / template_name
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Email template not found: {template_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading email template {template_name}: {str(e)}")
        raise


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.use_tls = settings.smtp_use_tls

        logger.info(f"Email service initialized with SMTP host: {self.smtp_host}:{self.smtp_port}")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text alternative (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            # Add plain text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=self.use_tls
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_verification_email(
        self,
        email: str,
        username: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification link

        Args:
            email: User email address
            username: Username
            verification_token: Verification token

        Returns:
            True if sent successfully
        """
        verification_link = f"{settings.frontend_url}/verify-email?token={verification_token}"

        template_content = load_email_template("01_verification_email.html")
        template = Template(template_content)
        html_content = template.render(
            username=username,
            verification_link=verification_link
        )

        return await self.send_email(
            to_email=email,
            subject="Bestätigen Sie Ihre E-Mail-Adresse - Baumaschinen-KI Chatbot",
            html_content=html_content,
            text_content=f"Bitte bestätigen Sie Ihre E-Mail, indem Sie folgenden Link besuchen: {verification_link}"
        )

    async def send_admin_notification(
        self,
        user_data: Dict[str, Any]
    ) -> bool:
        """
        Send notification to admin about new user pending approval

        Args:
            user_data: Dictionary with user information (username, email, created_at)

        Returns:
            True if sent successfully
        """
        admin_dashboard_link = f"{settings.frontend_url}/admin/users"

        template_content = load_email_template("02_admin_notification.html")
        template = Template(template_content)
        html_content = template.render(
            username=user_data.get("username"),
            email=user_data.get("email"),
            registration_date=user_data.get("created_at"),
            admin_dashboard_link=admin_dashboard_link
        )

        return await self.send_email(
            to_email=settings.admin_email,
            subject=f"Neuer Benutzer wartet auf Genehmigung: {user_data.get('username')}",
            html_content=html_content,
            text_content=f"Neuer Benutzer {user_data.get('username')} ({user_data.get('email')}) wartet auf Genehmigung."
        )

    async def send_approval_email(
        self,
        email: str,
        username: str,
        authorization_level: str
    ) -> bool:
        """
        Send account approval notification

        Args:
            email: User email address
            username: Username
            authorization_level: Assigned authorization level

        Returns:
            True if sent successfully
        """
        try:
            logger.debug(f"Preparing approval email for {username} ({email})")
            login_link = f"{settings.frontend_url}/login"
            logger.debug(f"Login link: {login_link}")

            template_content = load_email_template("03_approval_email.html")
            template = Template(template_content)
            logger.debug("Template loaded successfully")

            html_content = template.render(
                username=username,
                authorization_level=authorization_level.title(),
                login_link=login_link
            )
            logger.debug(f"Template rendered successfully, content length: {len(html_content)}")

            result = await self.send_email(
                to_email=email,
                subject="Ihr Konto wurde genehmigt!",
                html_content=html_content,
                text_content=f"Ihr Konto wurde mit {authorization_level}-Zugriff genehmigt. Sie können sich jetzt anmelden unter {login_link}"
            )
            logger.debug(f"send_email returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Exception in send_approval_email: {type(e).__name__}: {e}", exc_info=True)
            return False

    async def send_rejection_email(
        self,
        email: str,
        username: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Send account rejection notification

        Args:
            email: User email address
            username: Username
            reason: Optional rejection reason

        Returns:
            True if sent successfully
        """
        # Choose template based on whether reason is provided
        if reason:
            template_content = load_email_template("05a_rejection_email_with_reason.html")
        else:
            template_content = load_email_template("05b_rejection_email_without_reason.html")

        template = Template(template_content)
        html_content = template.render(
            username=username,
            reason=reason
        )

        return await self.send_email(
            to_email=email,
            subject="Aktualisierung zur Kontoregistrierung",
            html_content=html_content,
            text_content=f"Ihre Kontoregistrierung wurde nicht genehmigt. {f'Grund: {reason}' if reason else ''}"
        )

    async def send_password_reset_email(
        self,
        email: str,
        username: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email with secure link

        Args:
            email: User email address
            username: Username
            reset_token: Password reset token

        Returns:
            True if sent successfully
        """
        reset_link = f"{settings.frontend_url}/reset-password/{reset_token}"

        template_content = load_email_template("04_password_reset.html")
        template = Template(template_content)
        html_content = template.render(
            username=username,
            reset_link=reset_link
        )

        return await self.send_email(
            to_email=email,
            subject="Passwort zurücksetzen - Baumaschinen-KI Chatbot",
            html_content=html_content,
            text_content=f"Passwort zurücksetzen: Besuchen Sie folgenden Link: {reset_link} (Gültig für 1 Stunde)"
        )

    async def send_verification_success_email(
        self,
        email: str,
        username: str
    ) -> bool:
        """
        Send email verification success notification

        Args:
            email: User email address
            username: Username

        Returns:
            True if sent successfully
        """
        template = Template(VERIFICATION_SUCCESS_EMAIL_TEMPLATE)
        html_content = template.render(
            username=username
        )

        return await self.send_email(
            to_email=email,
            subject="E-Mail-Adresse erfolgreich bestätigt!",
            html_content=html_content,
            text_content=f"Ihre E-Mail-Adresse wurde erfolgreich bestätigt. Ihr Konto wartet nun auf die Genehmigung durch einen Administrator."
        )

    async def send_role_change_email(
        self,
        email: str,
        username: str,
        old_level: str,
        new_level: str
    ) -> bool:
        """
        Send role change notification

        Args:
            email: User email address
            username: Username
            old_level: Previous authorization level
            new_level: New authorization level

        Returns:
            True if sent successfully
        """
        # Simple inline HTML template for role change notification
        role_change_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2563eb; margin-top: 0;">Berechtigungsstufe geändert</h2>
                <p>Hallo {{ username }},</p>
                <p>Ihre Berechtigungsstufe wurde aktualisiert:</p>
                <div style="background-color: #fff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Bisherige Stufe:</strong> {{ old_level }}</p>
                    <p style="margin: 5px 0;"><strong>Neue Stufe:</strong> {{ new_level }}</p>
                </div>
                <p>Bei Fragen wenden Sie sich bitte an Ihren Administrator.</p>
                <p style="color: #6b7280; font-size: 0.9em; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    Ihr Baumaschinen-KI Team
                </p>
            </div>
        </body>
        </html>
        """

        template = Template(role_change_template)
        html_content = template.render(
            username=username,
            old_level=old_level.title(),
            new_level=new_level.title()
        )

        return await self.send_email(
            to_email=email,
            subject="Ihre Berechtigungsstufe wurde geändert",
            html_content=html_content,
            text_content=f"Ihre Berechtigungsstufe wurde von {old_level} zu {new_level} geändert."
        )


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get singleton Email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


# Standalone functions for direct imports (used by tests)
async def send_verification_email(
    email: str,
    username: str,
    verification_token: str
) -> bool:
    """
    Send email verification link (standalone function).

    Args:
        email: User email address
        username: Username
        verification_token: Verification token

    Returns:
        True if sent successfully

    Raises:
        ValueError: If email format is invalid
    """
    from app.utils.security import validate_email

    if not validate_email(email):
        raise ValueError(f"Invalid email address: {email}")

    service = get_email_service()
    return await service.send_verification_email(email, username, verification_token)


async def send_approval_email(
    email: str,
    username: str,
    authorization_level: str
) -> bool:
    """
    Send account approval notification (standalone function).

    Args:
        email: User email address
        username: Username
        authorization_level: Assigned authorization level

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    return await service.send_approval_email(email, username, authorization_level)


async def send_rejection_email(
    email: str,
    username: str,
    reason: Optional[str] = None
) -> bool:
    """
    Send account rejection notification (standalone function).

    Args:
        email: User email address
        username: Username
        reason: Optional rejection reason

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    return await service.send_rejection_email(email, username, reason)


async def send_admin_notification(
    admin_email: str,
    new_username: str,
    new_email: str
) -> bool:
    """
    Send notification to admin about new user pending approval (standalone function).

    Args:
        admin_email: Admin email address
        new_username: New user's username
        new_email: New user's email

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    user_data = {
        "username": new_username,
        "email": new_email,
        "created_at": datetime.utcnow().isoformat()
    }
    return await service.send_admin_notification(user_data)
