import os
import logging
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, receiver_email: Optional[str] = None) -> bool:
    """
    Send an email using the configured SMTP server.
    
    Args:
        subject: Email subject
        body: Email body content
        receiver_email: Optional recipient email address
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT', 587)
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    to_email = receiver_email or os.getenv('TO_EMAIL')
    
    # Check required variables
    if not all([smtp_server, smtp_port, smtp_username, smtp_password, from_email, to_email]):
        logger.error("Missing required SMTP configuration in environment variables")
        return False

    try:
        # Prepare the email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the email
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()  # Upgrade to a secure connection
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
            logger.info(f"Email sent successfully to {to_email}")
            return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
