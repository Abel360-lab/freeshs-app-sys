# Email Configuration Setup

## Overview
The system sends email notifications when applications are approved. To enable email notifications, you need to configure the email settings.

## Current Email Configuration
The system is currently configured to use SMTP email backend with the following settings:

- **Email Backend**: SMTP (smtp.gmail.com)
- **Port**: 587
- **TLS**: Enabled
- **From Email**: Uses EMAIL_HOST_USER or defaults to noreply@gcx.com.gh

## Setup Instructions

### Option 1: Gmail Setup (Recommended for Development)
1. Create a Gmail account for the system
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
4. Set environment variables:
   ```bash
   set EMAIL_HOST_USER=your-email@gmail.com
   set EMAIL_HOST_PASSWORD=your-app-password
   ```

### Option 2: Custom SMTP Server
1. Configure your SMTP server details:
   ```bash
   set EMAIL_HOST=your-smtp-server.com
   set EMAIL_PORT=587
   set EMAIL_USE_TLS=True
   set EMAIL_HOST_USER=your-email@yourdomain.com
   set EMAIL_HOST_PASSWORD=your-password
   set DEFAULT_FROM_EMAIL=your-email@yourdomain.com
   ```

### Option 3: Disable Email Notifications (Development)
If you don't want to set up email, the system will still work but will show a warning toast when email fails.

## Testing Email Configuration
You can test the email configuration by approving an application. The system will:
- ✅ Show success toast if email is sent successfully
- ⚠️ Show warning toast if email fails (but approval still works)
- ❌ Show error toast if there's a critical issue

## Email Content
The approval email includes:
- Application tracking code
- Business name
- Approval date and time
- Approver information
- Account activation status
- Additional notes (if provided)
- Supplier portal login link

## Troubleshooting
- **"Connection unexpectedly closed"**: Check SMTP credentials and network connection
- **"Email not configured"**: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD environment variables
- **Authentication failed**: Verify email credentials and app password (for Gmail)

## Production Setup
For production, consider:
- Using a dedicated email service (SendGrid, AWS SES, etc.)
- Setting up proper SPF/DKIM records
- Using environment variables for security
- Monitoring email delivery rates
