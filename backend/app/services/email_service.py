import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class EmailService:
    @staticmethod
    def send_otp_email(to_email: str, otp: str):
        """Send a 6-digit OTP to the provided email address."""
        if not settings.SMTP_SERVER or not settings.SMTP_USERNAME:
            logger.warning(
                "SMTP credentials not configured. OTP for %s is: %s",
                to_email, otp
            )
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your AgroGuard-AI Password Reset OTP"
            msg["From"] = settings.EMAIL_FROM_ADDRESS
            msg["To"] = to_email

            text = f"Your password reset OTP is: {otp}. It will expire in 10 minutes."
            html = f"""
            <html>
              <body>
                <h2>Password Reset Request</h2>
                <p>Your 6-digit OTP for resetting your AgroGuard-AI password is:</p>
                <h1 style="color: #2e7d32; letter-spacing: 5px;">{otp}</h1>
                <p>This code will expire in 10 minutes. If you did not request a password reset, please ignore this email.</p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.EMAIL_FROM_ADDRESS,
                    to_email,
                    msg.as_string()
                )
                
            logger.info("Successfully sent OTP email to %s", to_email)
        except Exception as exc:
            logger.error("Failed to send OTP email to %s: %s", to_email, exc)
            # Log the OTP as a fallback for development if email sending fails
            logger.info("Fallback - OTP for %s is: %s", to_email, otp)
