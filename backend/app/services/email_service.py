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
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Email templates
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Mail-Adresse bestätigen</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .button-container {
            text-align: center;
            margin: 35px 0;
        }

        .button {
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }

        .link-box {
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            word-break: break-all;
            font-size: 14px;
            color: #6b7280;
        }

        .info-box {
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 16px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .info-box p {
            margin: 0;
            color: #92400e;
            font-size: 15px;
        }

        .security-notice {
            background-color: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 16px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .security-notice p {
            margin: 0;
            color: #1e40af;
            font-size: 15px;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .button {
                padding: 14px 30px;
                font-size: 15px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <h1>Baumaschinen-KI</h1>
                <div class="subtitle">Powered by Rüko</div>
            </div>
            <div class="content">
                <h2>E-Mail-Adresse bestätigen</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p>vielen Dank für Ihre Registrierung bei der Baumaschinen-KI von Rüko.</p>
                <p>Um Ihr Konto zu aktivieren, bestätigen Sie bitte Ihre E-Mail-Adresse durch Klick auf die folgende Schaltfläche:</p>

                <div class="button-container">
                    <a href="{{ verification_link }}" class="button">E-Mail-Adresse bestätigen</a>
                </div>

                <p style="font-size: 14px; color: #6b7280;">Alternativ können Sie auch folgenden Link in Ihren Browser kopieren:</p>
                <div class="link-box">{{ verification_link }}</div>

                <div class="info-box">
                    <p><strong>Wichtig:</strong> Dieser Bestätigungslink ist 24 Stunden gültig.</p>
                </div>

                <div class="security-notice">
                    <p><strong>Sicherheitshinweis:</strong> Falls Sie sich nicht registriert haben, können Sie diese E-Mail ignorieren. Ihr Passwort bleibt geschützt.</p>
                </div>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

ADMIN_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neue Benutzerregistrierung - Genehmigung erforderlich</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 26px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 15px;
            opacity: 0.95;
            font-weight: 400;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .alert-badge {
            display: inline-block;
            background-color: #fef3c7;
            color: #92400e;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .user-details-box {
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .user-details-box h3 {
            color: #1f2937;
            font-size: 18px;
            margin: 0 0 20px 0;
            font-weight: 700;
        }

        .detail-item {
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }

        .detail-item:last-child {
            border-bottom: none;
        }

        .detail-label {
            font-weight: 600;
            color: #64748b;
            min-width: 180px;
            font-size: 15px;
        }

        .detail-value {
            color: #1f2937;
            font-weight: 500;
            font-size: 15px;
        }

        .button-container {
            text-align: center;
            margin: 35px 0;
        }

        .button {
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }

        .action-notice {
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 16px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .action-notice p {
            margin: 0;
            color: #92400e;
            font-size: 15px;
            font-weight: 500;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 22px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .user-details-box {
                padding: 20px;
            }

            .detail-item {
                flex-direction: column;
            }

            .detail-label {
                min-width: auto;
                margin-bottom: 4px;
            }

            .button {
                padding: 14px 30px;
                font-size: 15px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <h1>Neue Benutzerregistrierung</h1>
                <div class="subtitle">Genehmigung erforderlich</div>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="alert-badge">AKTION ERFORDERLICH</span>
                </div>

                <h2>Administrator-Benachrichtigung</h2>
                <p>Sehr geehrte Administration,</p>
                <p>ein neuer Benutzer hat sich erfolgreich registriert und die E-Mail-Verifizierung abgeschlossen. Der Benutzer wartet nun auf Ihre Genehmigung.</p>

                <div class="user-details-box">
                    <h3>Benutzer-Details</h3>
                    <div class="detail-item">
                        <div class="detail-label">Benutzername:</div>
                        <div class="detail-value">{{ username }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">E-Mail-Adresse:</div>
                        <div class="detail-value">{{ email }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Registriert am:</div>
                        <div class="detail-value">{{ registration_date }}</div>
                    </div>
                </div>

                <div class="action-notice">
                    <p><strong>Hinweis:</strong> Bitte prüfen Sie die Registrierung und treffen Sie eine Entscheidung über die Genehmigung oder Ablehnung.</p>
                </div>

                <p style="text-align: center; margin-top: 30px;">Öffnen Sie das Admin-Dashboard, um den Benutzer zu genehmigen oder abzulehnen:</p>

                <div class="button-container">
                    <a href="{{ admin_dashboard_link }}" class="button">Zum Admin-Dashboard</a>
                </div>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI Admin-System</p>
                <p>Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

APPROVAL_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ihr Konto wurde genehmigt</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .success-badge {
            display: inline-block;
            background-color: #d1fae5;
            color: #065f46;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .celebration-icon {
            font-size: 48px;
            margin: 20px 0;
        }

        .info-highlight {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
            border-radius: 10px;
            padding: 20px 25px;
            margin: 30px 0;
            text-align: center;
        }

        .info-highlight p {
            margin: 0;
            color: #065f46;
            font-size: 16px;
        }

        .info-highlight .level {
            font-size: 20px;
            font-weight: 700;
            color: #059669;
            margin-top: 8px;
        }

        .button-container {
            text-align: center;
            margin: 35px 0;
        }

        .button {
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }

        .welcome-message {
            background-color: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 16px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .welcome-message p {
            margin: 0;
            color: #1e40af;
            font-size: 15px;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .info-highlight {
                padding: 16px 20px;
            }

            .button {
                padding: 14px 30px;
                font-size: 15px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <div class="celebration-icon">✓</div>
                <h1>Konto genehmigt!</h1>
                <div class="subtitle">Willkommen bei der Baumaschinen-KI</div>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="success-badge">ERFOLGREICH GENEHMIGT</span>
                </div>

                <h2>Herzlich willkommen</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p><strong>Gute Nachrichten!</strong> Ihr Konto wurde von unserem Administrator genehmigt.</p>
                <p>Sie können sich jetzt anmelden und alle Funktionen der Baumaschinen-KI von Rüko nutzen.</p>

                <div class="info-highlight">
                    <p>Ihre Autorisierungsebene:</p>
                    <div class="level">{{ authorization_level }}</div>
                </div>

                <p style="text-align: center; font-size: 17px; font-weight: 500;">Starten Sie jetzt mit der Baumaschinen-KI:</p>

                <div class="button-container">
                    <a href="{{ login_link }}" class="button">Jetzt anmelden</a>
                </div>

                <div class="welcome-message">
                    <p><strong>Willkommen an Bord!</strong> Wir freuen uns, Sie in unserem System begrüßen zu dürfen. Bei Fragen oder Unterstützungsbedarf stehen wir Ihnen gerne zur Verfügung.</p>
                </div>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Bei Fragen kontaktieren Sie bitte Ihren Administrator.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passwort zurücksetzen</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .header .lock-icon {
            font-size: 42px;
            margin-bottom: 15px;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .button-container {
            text-align: center;
            margin: 35px 0;
        }

        .button {
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }

        .link-box {
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            word-break: break-all;
            font-size: 14px;
            color: #6b7280;
        }

        .warning-box {
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 18px 22px;
            margin: 30px 0;
            border-radius: 4px;
        }

        .warning-box p {
            margin: 0;
            color: #92400e;
            font-size: 15px;
            font-weight: 500;
        }

        .warning-box .warning-title {
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 8px;
            display: block;
        }

        .security-notice {
            background-color: #f0f9ff;
            border: 2px solid #2563eb;
            border-radius: 8px;
            padding: 20px 25px;
            margin: 30px 0;
        }

        .security-notice h3 {
            color: #1e40af;
            font-size: 17px;
            font-weight: 700;
            margin: 0 0 12px 0;
        }

        .security-notice ul {
            margin: 0;
            padding-left: 20px;
            color: #1e40af;
        }

        .security-notice li {
            margin: 8px 0;
            font-size: 15px;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .button {
                padding: 14px 30px;
                font-size: 15px;
            }

            .security-notice {
                padding: 16px 20px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <div class="lock-icon">🔒</div>
                <h1>Passwort zurücksetzen</h1>
                <div class="subtitle">Baumaschinen-KI Sicherheit</div>
            </div>
            <div class="content">
                <h2>Passwort-Zurücksetzung angefordert</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.</p>
                <p>Klicken Sie auf die folgende Schaltfläche, um ein neues Passwort festzulegen:</p>

                <div class="button-container">
                    <a href="{{ reset_link }}" class="button">Neues Passwort festlegen</a>
                </div>

                <p style="font-size: 14px; color: #6b7280;">Alternativ können Sie auch folgenden Link in Ihren Browser kopieren:</p>
                <div class="link-box">{{ reset_link }}</div>

                <div class="warning-box">
                    <span class="warning-title">⏱ Zeitlich begrenzt</span>
                    <p>Dieser Link ist nur 1 Stunde gültig. Nach Ablauf müssen Sie eine neue Anfrage stellen.</p>
                </div>

                <div class="security-notice">
                    <h3>Sicherheitshinweise:</h3>
                    <ul>
                        <li>Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail. Ihr Passwort bleibt unverändert.</li>
                        <li>Der Link wird nach einmaliger Verwendung automatisch ungültig.</li>
                        <li>Teilen Sie diesen Link niemals mit anderen Personen.</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

REJECTION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrierung nicht genehmigt</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 26px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .status-message {
            background-color: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
        }

        .status-message p {
            margin: 0;
            color: #64748b;
            font-size: 16px;
            font-weight: 500;
        }

        .reason-box {
            background-color: #fff7ed;
            border-left: 4px solid #f59e0b;
            padding: 20px 25px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .reason-box .reason-label {
            font-weight: 700;
            color: #92400e;
            font-size: 16px;
            display: block;
            margin-bottom: 8px;
        }

        .reason-box .reason-text {
            color: #92400e;
            font-size: 15px;
            line-height: 1.6;
            margin: 0;
        }

        .contact-box {
            background-color: #f0f9ff;
            border: 2px solid #2563eb;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
        }

        .contact-box h3 {
            color: #1e40af;
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 15px 0;
        }

        .contact-box p {
            margin: 10px 0;
            color: #1e40af;
            font-size: 15px;
        }

        .contact-email {
            display: inline-block;
            color: #2563eb;
            font-weight: 600;
            text-decoration: none;
            font-size: 16px;
            padding: 8px 16px;
            background-color: #dbeafe;
            border-radius: 6px;
            margin-top: 8px;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 22px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .status-message,
            .reason-box,
            .contact-box {
                padding: 20px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <h1>Registrierung nicht genehmigt</h1>
                <div class="subtitle">Baumaschinen-KI</div>
            </div>
            <div class="content">
                <h2>Aktualisierung zur Kontoregistrierung</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p>vielen Dank für Ihr Interesse an der Baumaschinen-KI von Rüko.</p>

                <div class="status-message">
                    <p>Leider können wir Ihre Registrierung derzeit nicht genehmigen.</p>
                </div>

                {% if reason %}
                <div class="reason-box">
                    <span class="reason-label">Grund der Ablehnung:</span>
                    <p class="reason-text">{{ reason }}</p>
                </div>
                {% endif %}

                <p>Falls Sie der Meinung sind, dass es sich um einen Fehler handelt oder Sie weitere Informationen benötigen, wenden Sie sich bitte an unseren Support.</p>

                <div class="contact-box">
                    <h3>Kontakt & Support</h3>
                    <p>Bei Fragen oder Unklarheiten stehen wir Ihnen gerne zur Verfügung:</p>
                    <a href="mailto:support@rueko.de" class="contact-email">support@rueko.de</a>
                </div>

                <p style="color: #6b7280; font-size: 15px; margin-top: 30px;">Wir bedauern, dass wir Ihnen keine positivere Nachricht übermitteln können, und danken Ihnen für Ihr Verständnis.</p>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

VERIFICATION_SUCCESS_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Mail-Adresse bestätigt</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .header .success-icon {
            font-size: 52px;
            margin-bottom: 15px;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .success-badge {
            display: inline-block;
            background-color: #d1fae5;
            color: #065f46;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .info-highlight {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
        }

        .info-highlight .step-label {
            color: #065f46;
            font-weight: 700;
            font-size: 18px;
            display: block;
            margin-bottom: 10px;
        }

        .info-highlight p {
            margin: 8px 0;
            color: #047857;
            font-size: 16px;
        }

        .next-steps-box {
            background-color: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 20px 25px;
            margin: 30px 0;
            border-radius: 4px;
        }

        .next-steps-box h3 {
            color: #1e40af;
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 15px 0;
        }

        .next-steps-box ol {
            margin: 0;
            padding-left: 20px;
            color: #1e40af;
        }

        .next-steps-box li {
            margin: 10px 0;
            font-size: 15px;
            line-height: 1.5;
        }

        .timeline-box {
            background-color: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 10px;
            padding: 20px 25px;
            margin: 25px 0;
        }

        .timeline-box p {
            margin: 0;
            color: #92400e;
            font-size: 15px;
            font-weight: 500;
        }

        .timeline-box .timeline-icon {
            font-size: 24px;
            margin-bottom: 8px;
            display: block;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .info-highlight {
                padding: 20px;
            }

            .next-steps-box,
            .timeline-box {
                padding: 16px 20px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <div class="success-icon">✓</div>
                <h1>E-Mail-Adresse bestätigt!</h1>
                <div class="subtitle">Baumaschinen-KI</div>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="success-badge">ERFOLGREICH BESTÄTIGT</span>
                </div>

                <h2>Bestätigung erhalten</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p><strong>Vielen Dank!</strong> Ihre E-Mail-Adresse wurde erfolgreich bestätigt.</p>

                <div class="info-highlight">
                    <span class="step-label">Schritt 1 von 2 abgeschlossen</span>
                    <p>Ihre E-Mail-Verifizierung ist erfolgt!</p>
                </div>

                <div class="next-steps-box">
                    <h3>Was passiert jetzt?</h3>
                    <ol>
                        <li><strong>Admin-Prüfung:</strong> Unsere Administratoren wurden über Ihre Registrierung benachrichtigt und werden Ihr Konto zeitnah prüfen.</li>
                        <li><strong>Genehmigung:</strong> Nach erfolgreicher Prüfung erhalten Sie eine E-Mail zur Konto-Genehmigung.</li>
                        <li><strong>Anmeldung:</strong> Sobald Ihr Konto genehmigt ist, können Sie sich anmelden und alle Funktionen nutzen.</li>
                    </ol>
                </div>

                <div class="timeline-box">
                    <span class="timeline-icon">⏱</span>
                    <p><strong>Bearbeitungszeit:</strong> Die Genehmigung erfolgt in der Regel innerhalb von 24-48 Stunden während der Geschäftszeiten.</p>
                </div>

                <p style="text-align: center; color: #059669; font-weight: 600; font-size: 17px; margin-top: 30px;">Sie werden per E-Mail benachrichtigt, sobald Ihr Konto genehmigt wurde.</p>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Bei Fragen kontaktieren Sie uns gerne unter support@rueko.de</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

ROLE_CHANGE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Berechtigungsstufe geändert</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
        }

        .email-wrapper {
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }

        .header .icon {
            font-size: 48px;
            margin-bottom: 15px;
        }

        .content {
            padding: 45px 40px;
            background-color: #ffffff;
        }

        .content h2 {
            color: #1f2937;
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 25px 0;
        }

        .content p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.7;
            margin: 0 0 20px 0;
        }

        .greeting {
            color: #1f2937;
            font-weight: 600;
            font-size: 17px;
        }

        .notification-badge {
            display: inline-block;
            background-color: #ede9fe;
            color: #6b21a8;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .change-box {
            background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
            border: 2px solid #8b5cf6;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }

        .change-box .change-title {
            color: #6b21a8;
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 20px;
            display: block;
        }

        .level-comparison {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
        }

        .level-badge {
            background-color: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px 25px;
            font-weight: 700;
            font-size: 18px;
            color: #64748b;
        }

        .level-badge.new {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            border: none;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        }

        .arrow {
            font-size: 24px;
            color: #8b5cf6;
            font-weight: 700;
        }

        .info-box {
            background-color: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 20px 25px;
            margin: 30px 0;
            border-radius: 4px;
        }

        .info-box h3 {
            color: #1e40af;
            font-size: 17px;
            font-weight: 700;
            margin: 0 0 12px 0;
        }

        .info-box ul {
            margin: 0;
            padding-left: 20px;
            color: #1e40af;
        }

        .info-box li {
            margin: 8px 0;
            font-size: 15px;
        }

        .security-notice {
            background-color: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 8px;
            padding: 18px 22px;
            margin: 30px 0;
        }

        .security-notice p {
            margin: 0;
            color: #92400e;
            font-size: 15px;
            font-weight: 500;
        }

        .security-notice .security-icon {
            font-size: 20px;
            margin-right: 8px;
        }

        .footer {
            background-color: #f9fafb;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }

        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin: 8px 0;
        }

        .footer .brand {
            font-weight: 600;
            color: #2563eb;
            font-size: 15px;
        }

        .footer .company {
            color: #4b5563;
            font-weight: 500;
        }

        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
                margin: 0;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .content {
                padding: 30px 20px;
            }

            .content h2 {
                font-size: 20px;
            }

            .change-box {
                padding: 20px;
            }

            .level-comparison {
                flex-direction: column;
                gap: 10px;
            }

            .arrow {
                transform: rotate(90deg);
            }

            .level-badge {
                padding: 12px 20px;
                font-size: 16px;
            }

            .info-box,
            .security-notice {
                padding: 16px 20px;
            }

            .footer {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="header">
                <div class="icon">🔐</div>
                <h1>Berechtigungsstufe geändert</h1>
                <div class="subtitle">Baumaschinen-KI Sicherheitsbenachrichtigung</div>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="notification-badge">BERECHTIGUNGSÄNDERUNG</span>
                </div>

                <h2>Kontoaktualisierung</h2>
                <p class="greeting">Hallo {{ username }},</p>
                <p>Ihre Berechtigungsstufe im Baumaschinen-KI System wurde von einem Administrator geändert.</p>

                <div class="change-box">
                    <span class="change-title">Änderung Ihrer Autorisierung</span>
                    <div class="level-comparison">
                        <div class="level-badge">{{ old_level }}</div>
                        <div class="arrow">→</div>
                        <div class="level-badge new">{{ new_level }}</div>
                    </div>
                </div>

                <div class="info-box">
                    <h3>Was bedeutet das für Sie?</h3>
                    <ul>
                        <li>Ihre neue Berechtigungsstufe wird beim nächsten Login wirksam</li>
                        <li>Zugriffsrechte und verfügbare Funktionen können sich geändert haben</li>
                        <li>Die Änderung wurde aus Sicherheitsgründen protokolliert</li>
                    </ul>
                </div>

                <div class="security-notice">
                    <p><span class="security-icon">🛡</span><strong>Sicherheitshinweis:</strong> Diese Änderung wurde von einem autorisierten Administrator durchgeführt. Falls Sie Fragen zu dieser Änderung haben oder diese nicht nachvollziehen können, kontaktieren Sie bitte umgehend Ihren Administrator.</p>
                </div>

                <p style="text-align: center; color: #6b7280; font-size: 15px; margin-top: 30px;">Diese Änderung tritt mit Ihrer nächsten Anmeldung in Kraft.</p>
            </div>
            <div class="footer">
                <p class="brand">Baumaschinen-KI</p>
                <p class="company">Rüko GmbH &copy; 2025</p>
                <p style="margin-top: 15px;">Bei Fragen kontaktieren Sie bitte Ihren Administrator.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


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

        template = Template(VERIFICATION_EMAIL_TEMPLATE)
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

        template = Template(ADMIN_NOTIFICATION_TEMPLATE)
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

            template = Template(APPROVAL_EMAIL_TEMPLATE)
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
        template = Template(REJECTION_EMAIL_TEMPLATE)
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

        template = Template(PASSWORD_RESET_EMAIL_TEMPLATE)
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
        template = Template(ROLE_CHANGE_EMAIL_TEMPLATE)
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
