"""
Email Service Module for OTP and Notifications
Uses Gmail SMTP by default. Configure via environment variables.

Required Environment Variables:
- EMAIL_ADDRESS: Your Gmail address (e.g., your.email@gmail.com)
- EMAIL_PASSWORD: Your Gmail App Password (NOT your regular password!)

To get Gmail App Password:
1. Enable 2-Step Verification at https://myaccount.google.com/security
2. Go to App passwords
3. Generate a new app password for "Mail"
4. Use that password here
"""

import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Configuration - Can be overridden by environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "CyberSafe Portal")


def is_email_configured() -> bool:
    """Check if email credentials are configured."""
    return bool(EMAIL_ADDRESS and EMAIL_PASSWORD)


def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body of the email
        text_content: Plain text fallback (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not is_email_configured():
        print("[EMAIL] Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
        message["To"] = to_email
        
        # Add plain text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, "plain")
            message.attach(part1)
        
        part2 = MIMEText(html_content, "html")
        message.attach(part2)
        
        # Create secure connection and send
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        
        print(f"[EMAIL] Successfully sent email to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"[EMAIL] Authentication failed. Check your email and app password.")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] Error sending email: {e}")
        return False


def send_otp_email(to_email: str, otp_code: str, purpose: str = "verification") -> bool:
    """
    Send OTP email with styled template.
    
    Args:
        to_email: Recipient email address
        otp_code: 6-digit OTP code
        purpose: "verification" for registration, "login" for login OTP
    
    Returns:
        True if email sent successfully, False otherwise
    """
    
    if purpose == "login":
        subject = "🔐 Your CyberSafe Login OTP"
        action_text = "login to your account"
    else:
        subject = "✅ Verify Your CyberSafe Account"
        action_text = "verify your email address"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border-radius: 16px 16px 0 0; padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🛡️ CyberSafe</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0;">Cybercrime Complaint Portal</p>
                </td>
            </tr>
            <tr>
                <td style="background: white; padding: 40px 30px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <h2 style="color: #1e3a5f; margin: 0 0 20px;">Your One-Time Password</h2>
                    <p style="color: #64748b; font-size: 16px; line-height: 1.6;">
                        Use the following OTP to {action_text}. This code will expire in <strong>10 minutes</strong>.
                    </p>
                    
                    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 2px dashed #0ea5e9; border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center;">
                        <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #0369a1; font-family: 'Courier New', monospace;">
                            {otp_code}
                        </span>
                    </div>
                    
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 30px;">
                        ⚠️ If you didn't request this OTP, please ignore this email or contact support if you have concerns.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                    
                    <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                        This is an automated message from CyberSafe Portal.<br>
                        Please do not reply to this email.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    text_content = f"""
    CyberSafe - One-Time Password
    
    Your OTP to {action_text} is: {otp_code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this OTP, please ignore this email.
    
    - CyberSafe Team
    """
    
    return send_email(to_email, subject, html_content, text_content)


def send_notification_email(to_email: str, title: str, message: str) -> bool:
    """Send a general notification email."""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border-radius: 16px 16px 0 0; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">🛡️ CyberSafe</h1>
                </td>
            </tr>
            <tr>
                <td style="background: white; padding: 30px; border-radius: 0 0 16px 16px;">
                    <h2 style="color: #1e3a5f; margin: 0 0 15px;">{title}</h2>
                    <p style="color: #64748b; font-size: 16px; line-height: 1.6;">{message}</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return send_email(to_email, f"CyberSafe: {title}", html_content, message)
