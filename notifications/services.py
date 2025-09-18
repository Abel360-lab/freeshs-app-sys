"""
Notification services for sending emails and SMS.
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from .models import NotificationLog, NotificationTemplate, SMSNotification
from core.models import AuditLog

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    def queue_notification(notification_log):
        """Queue a notification for background processing."""
        try:
            # Import here to avoid circular import
            from .tasks import send_notification_async
            
            # Queue the notification for background processing
            send_notification_async.delay(notification_log.id)
            logger.info(f"Queued notification {notification_log.id} for background processing")
            return True
        except Exception as e:
            logger.error(f"Error queuing notification {notification_log.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_document_request_notification(application, outstanding_request, request=None):
        """Send notification to applicant about missing documents."""
        try:
            # Get or create template
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.DOCUMENTS_REQUESTED,
                defaults={
                    'name': 'Document Request Notification',
                    'subject': 'Additional Documents Required - {{ business_name }}',
                    'body_html': '''
                    <h2>Additional Documents Required</h2>
                    <p>Dear {{ business_name }},</p>
                    <p>We have reviewed your supplier application and need additional documents to complete the process.</p>
                    
                    <h3>Missing Documents:</h3>
                    <ul>
                    {% for doc in missing_documents %}
                        <li>{{ doc }}</li>
                    {% endfor %}
                    </ul>
                    
                    <p><strong>Message from our team:</strong><br>
                    {{ message }}</p>
                    
                    <h3>Next Steps:</h3>
                    <p>Please click the link below to upload the missing documents:</p>
                    <p><a href="{{ submission_link }}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Upload Documents</a></p>
                    
                    <p><strong>Important:</strong> This link is secure and will expire in 30 days.</p>
                    
                    <p>If you have any questions, please contact us at support@gcx.com</p>
                    
                    <p>Best regards,<br>
                    GCX Supplier Application Team</p>
                    ''',
                    'body_text': '''
                    Additional Documents Required
                    
                    Dear {{ business_name }},
                    
                    We have reviewed your supplier application and need additional documents to complete the process.
                    
                    Missing Documents:
                    {% for doc in missing_documents %}
                    - {{ doc }}
                    {% endfor %}
                    
                    Message from our team:
                    {{ message }}
                    
                    Next Steps:
                    Please visit the following link to upload the missing documents:
                    {{ submission_link }}
                    
                    Important: This link is secure and will expire in 30 days.
                    
                    If you have any questions, please contact us at support@gcx.com
                    
                    Best regards,
                    GCX Supplier Application Team
                    '''
                }
            )
            
            # Prepare context data
            context_data = {
                'business_name': application.business_name,
                'tracking_code': application.tracking_code,
                'missing_documents': [req.label for req in outstanding_request.requirements.all()],
                'message': outstanding_request.message,
                'submission_link': request.build_absolute_uri(
                    reverse('applications:document-submission', kwargs={'token': application.completion_token})
                ) if request else f"http://localhost:8000/submit/{application.completion_token}/",
                'application_date': application.created_at.strftime('%B %d, %Y'),
                'requested_by': outstanding_request.requested_by.get_full_name() or outstanding_request.requested_by.username,
                'requested_date': outstanding_request.created_at.strftime('%B %d, %Y at %I:%M %p'),
            }
            
            # Render templates with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context_data))
            rendered_body_html = body_html_template.render(Context(context_data))
            rendered_body_text = body_text_template.render(Context(context_data))
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                template=template,
                channel=NotificationLog.Channel.EMAIL,
                recipient_email=application.email,
                recipient_name=application.business_name,
                subject=rendered_subject,
                body_html=rendered_body_html,
                body_text=rendered_body_text,
                context_data=context_data,
                application=application,
                ip_address=AuditLog.get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            )
            
            # Queue email for background processing
            if NotificationService.queue_notification(notification_log):
                logger.info(f"Document request notification queued for {application.email} for application {application.tracking_code}")
                return notification_log
            else:
                # Mark as failed
                notification_log.mark_failed("Failed to queue notification")
                logger.error(f"Failed to queue document request notification to {application.email}")
                raise Exception("Failed to queue notification")
                
        except Exception as e:
            logger.error(f"Error creating document request notification: {str(e)}")
            raise e
    
    @staticmethod
    def send_application_approval_notification(application, request=None):
        """Send notification when application is approved."""
        try:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.APPLICATION_APPROVED,
                defaults={
                    'name': 'Application Approval Notification',
                    'subject': 'Congratulations! Your Application Has Been Approved - {{ business_name }}',
                    'body_html': '''
                    <h2>Application Approved!</h2>
                    <p>Dear {{ business_name }},</p>
                    <p>Congratulations! Your supplier application has been approved.</p>
                    
                    <h3>Application Details:</h3>
                    <ul>
                        <li><strong>Business Name:</strong> {{ business_name }}</li>
                        <li><strong>Tracking Code:</strong> {{ tracking_code }}</li>
                        <li><strong>Application Date:</strong> {{ application_date }}</li>
                        <li><strong>Approved Date:</strong> {{ approved_date }}</li>
                    </ul>
                    
                    <p><strong>Next Steps:</strong></p>
                    <p>You will receive further instructions via email regarding your supplier account setup and onboarding process.</p>
                    
                    <p>If you have any questions, please contact us at support@gcx.com</p>
                    
                    <p>Welcome to the GCX supplier family!</p>
                    
                    <p>Best regards,<br>
                    GCX Supplier Application Team</p>
                    ''',
                    'body_text': '''
                    Application Approved!
                    
                    Dear {{ business_name }},
                    
                    Congratulations! Your supplier application has been approved.
                    
                    Application Details:
                    - Business Name: {{ business_name }}
                    - Tracking Code: {{ tracking_code }}
                    - Application Date: {{ application_date }}
                    - Approved Date: {{ approved_date }}
                    
                    Next Steps:
                    You will receive further instructions via email regarding your supplier account setup and onboarding process.
                    
                    If you have any questions, please contact us at support@gcx.com
                    
                    Welcome to the GCX supplier family!
                    
                    Best regards,
                    GCX Supplier Application Team
                    '''
                }
            )
            
            context_data = {
                'business_name': application.business_name,
                'tracking_code': application.tracking_code,
                'application_date': application.created_at.strftime('%B %d, %Y'),
                'approved_date': application.approved_at.strftime('%B %d, %Y at %I:%M %p') if application.approved_at else 'N/A',
            }
            
            # Render templates with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context_data))
            rendered_body_html = body_html_template.render(Context(context_data))
            rendered_body_text = body_text_template.render(Context(context_data))
            
            notification_log = NotificationLog.objects.create(
                template=template,
                channel=NotificationLog.Channel.EMAIL,
                recipient_email=application.email,
                recipient_name=application.business_name,
                subject=rendered_subject,
                body_html=rendered_body_html,
                body_text=rendered_body_text,
                context_data=context_data,
                application=application,
                ip_address=AuditLog.get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            )
            
            try:
                send_mail(
                    subject=notification_log.subject,
                    message=notification_log.body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification_log.recipient_email],
                    html_message=notification_log.body_html,
                    fail_silently=False,
                )
                
                notification_log.mark_sent()
                logger.info(f"Application approval notification sent to {application.email} for application {application.tracking_code}")
                return notification_log
                
            except Exception as e:
                notification_log.mark_failed(str(e))
                logger.error(f"Failed to send approval notification to {application.email}: {str(e)}")
                raise e
                
        except Exception as e:
            logger.error(f"Error creating approval notification: {str(e)}")
            raise e
    
    @staticmethod
    def send_application_approval_with_credentials(application, user, password, request=None):
        """Send notification when application is approved with login credentials."""
        try:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.APPLICATION_APPROVED,
                defaults={
                    'name': 'Application Approval with Credentials',
                    'subject': 'Welcome! Your Application Approved & Account Created - {{ business_name }}',
                    'body_html': '''
                    <h2>Congratulations! Your Application Has Been Approved</h2>
                    <p>Dear {{ business_name }},</p>
                    
                    <p>We are pleased to inform you that your supplier application has been <strong>approved</strong>!</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Your Account Details</h3>
                        <p><strong>Email:</strong> {{ user_email }}</p>
                        <p><strong>Username:</strong> {{ user_email }}</p>
                        <p><strong>Temporary Password:</strong> <code style="background-color: #e9ecef; padding: 4px 8px; border-radius: 4px;">{{ temp_password }}</code></p>
                    </div>
                    
                    <h3>Next Steps:</h3>
                    <ol>
                        <li><strong>Login to your account:</strong> Use the credentials above to access your supplier portal</li>
                        <li><strong>Change your password:</strong> For security, please change your password immediately after first login</li>
                        <li><strong>Complete your profile:</strong> Update your business information and preferences</li>
                        <li><strong>Start trading:</strong> Begin using the GCX platform for your commodity trading needs</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ login_url }}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Login to Your Account</a>
                    </div>
                    
                    <h3>Important Security Notes:</h3>
                    <ul>
                        <li>Keep your login credentials secure and do not share them with anyone</li>
                        <li>Change your password immediately after first login</li>
                        <li>Use a strong, unique password that you haven't used elsewhere</li>
                        <li>If you suspect any unauthorized access, contact us immediately</li>
                    </ul>
                    
                    <p><strong>Application Details:</strong></p>
                    <ul>
                        <li><strong>Tracking Code:</strong> {{ tracking_code }}</li>
                        <li><strong>Business Name:</strong> {{ business_name }}</li>
                        <li><strong>Approved On:</strong> {{ approved_date }}</li>
                    </ul>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Welcome to the GCX family!</p>
                    <p><strong>GCX Supplier Application Team</strong></p>
                    ''',
                    'body_text': '''
                    Congratulations! Your Application Has Been Approved
                    
                    Dear {{ business_name }},
                    
                    We are pleased to inform you that your supplier application has been approved!
                    
                    Your Account Details:
                    Email: {{ user_email }}
                    Username: {{ user_email }}
                    Temporary Password: {{ temp_password }}
                    
                    Next Steps:
                    1. Login to your account using the credentials above
                    2. Change your password immediately for security
                    3. Complete your profile
                    4. Start trading on the GCX platform
                    
                    Login URL: {{ login_url }}
                    
                    Application Details:
                    - Tracking Code: {{ tracking_code }}
                    - Business Name: {{ business_name }}
                    - Approved On: {{ approved_date }}
                    
                    Important: Keep your credentials secure and change your password after first login.
                    
                    Welcome to GCX!
                    GCX Supplier Application Team
                    '''
                }
            )
            
            # Prepare context data
            from django.template import Template, Context
            context_data = {
                'business_name': application.business_name,
                'user_email': user.email,
                'temp_password': password,
                'tracking_code': application.tracking_code,
                'approved_date': application.approved_at.strftime('%B %d, %Y') if application.approved_at else 'Today',
                'login_url': request.build_absolute_uri(reverse('accounts:login')) if request else "http://localhost:8000/accounts/login/",
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@gcx.com'),
                'company_name': 'GCX',
                'approval_comment': application.reviewer_comment or 'Your application has been reviewed and approved.'
            }
            
            # Render templates
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context_data))
            rendered_body_html = body_html_template.render(Context(context_data))
            rendered_body_text = body_text_template.render(Context(context_data))
            
            # Create notification log
            notification_log = NotificationLog.objects.create(
                template=template,
                recipient_email=application.email,
                recipient_name=application.business_name,
                subject=rendered_subject,
                body_html=rendered_body_html,
                body_text=rendered_body_text,
                channel=NotificationLog.Channel.EMAIL,
                status=NotificationLog.Status.PENDING,
                application=application,
                user=user,
                ip_address=AuditLog.get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
                metadata={
                    'application_tracking_code': application.tracking_code,
                    'user_created': True,
                    'credentials_sent': True
                }
            )
            
            # Send email
            send_mail(
                subject=rendered_subject,
                message=rendered_body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=rendered_body_html,
                fail_silently=False,
            )
            
            notification_log.mark_sent()
            logger.info(f"Application approval notification with credentials sent to {application.email} for application {application.tracking_code}")
            return notification_log
            
        except Exception as e:
            logger.error(f"Error creating approval notification with credentials: {str(e)}")
            raise e
    
    @staticmethod
    def send_application_rejection_notification(application, reason, request=None):
        """Send notification when application is rejected."""
        try:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=NotificationTemplate.NotificationType.APPLICATION_REJECTED,
                defaults={
                    'name': 'Application Rejection Notification',
                    'subject': 'Application Update - {{ business_name }}',
                    'body_html': '''
                    <h2>Application Update</h2>
                    <p>Dear {{ business_name }},</p>
                    <p>Thank you for your interest in becoming a GCX supplier. After careful review, we regret to inform you that your application has not been approved at this time.</p>
                    
                    <h3>Application Details:</h3>
                    <ul>
                        <li><strong>Business Name:</strong> {{ business_name }}</li>
                        <li><strong>Tracking Code:</strong> {{ tracking_code }}</li>
                        <li><strong>Application Date:</strong> {{ application_date }}</li>
                    </ul>
                    
                    <h3>Reason for Rejection:</h3>
                    <p>{{ reason }}</p>
                    
                    <p>We encourage you to address the issues mentioned above and reapply in the future. You may submit a new application at any time.</p>
                    
                    <p>If you have any questions or need clarification, please contact us at support@gcx.com</p>
                    
                    <p>Thank you for your interest in GCX.</p>
                    
                    <p>Best regards,<br>
                    GCX Supplier Application Team</p>
                    ''',
                    'body_text': '''
                    Application Update
                    
                    Dear {{ business_name }},
                    
                    Thank you for your interest in becoming a GCX supplier. After careful review, we regret to inform you that your application has not been approved at this time.
                    
                    Application Details:
                    - Business Name: {{ business_name }}
                    - Tracking Code: {{ tracking_code }}
                    - Application Date: {{ application_date }}
                    
                    Reason for Rejection:
                    {{ reason }}
                    
                    We encourage you to address the issues mentioned above and reapply in the future. You may submit a new application at any time.
                    
                    If you have any questions or need clarification, please contact us at support@gcx.com
                    
                    Thank you for your interest in GCX.
                    
                    Best regards,
                    GCX Supplier Application Team
                    '''
                }
            )
            
            context_data = {
                'business_name': application.business_name,
                'tracking_code': application.tracking_code,
                'application_date': application.created_at.strftime('%B %d, %Y'),
                'reason': reason,
            }
            
            # Render templates with context
            from django.template import Template, Context
            subject_template = Template(template.subject)
            body_html_template = Template(template.body_html)
            body_text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(Context(context_data))
            rendered_body_html = body_html_template.render(Context(context_data))
            rendered_body_text = body_text_template.render(Context(context_data))
            
            notification_log = NotificationLog.objects.create(
                template=template,
                channel=NotificationLog.Channel.EMAIL,
                recipient_email=application.email,
                recipient_name=application.business_name,
                subject=rendered_subject,
                body_html=rendered_body_html,
                body_text=rendered_body_text,
                context_data=context_data,
                application=application,
                ip_address=AuditLog.get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            )
            
            try:
                send_mail(
                    subject=notification_log.subject,
                    message=notification_log.body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification_log.recipient_email],
                    html_message=notification_log.body_html,
                    fail_silently=False,
                )
                
                notification_log.mark_sent()
                logger.info(f"Application rejection notification sent to {application.email} for application {application.tracking_code}")
                return notification_log
                
            except Exception as e:
                notification_log.mark_failed(str(e))
                logger.error(f"Failed to send rejection notification to {application.email}: {str(e)}")
                raise e
                
        except Exception as e:
            logger.error(f"Error creating rejection notification: {str(e)}")
            raise e
