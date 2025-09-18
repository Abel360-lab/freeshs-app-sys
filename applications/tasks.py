"""
Background tasks for supplier applications.
"""

import logging
from django.conf import settings
from django.utils import timezone
from .pdf_service import ApplicationPDFService
from .models import SupplierApplication

logger = logging.getLogger(__name__)


def generate_application_pdf_task(application_id):
    """
    Background task to generate PDF for an application.
    
    Args:
        application_id (int): ID of the application to generate PDF for
    """
    try:
        # Get the application
        application = SupplierApplication.objects.get(id=application_id)
        
        # Generate PDF
        pdf_service = ApplicationPDFService()
        file_path = pdf_service.generate_application_pdf(application)
        
        logger.info(f"PDF generated successfully for application {application_id}: {file_path}")
        
        return {
            'success': True,
            'file_path': file_path,
            'application_id': application_id
        }
        
    except SupplierApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found for PDF generation")
        return {
            'success': False,
            'error': 'Application not found',
            'application_id': application_id
        }
        
    except Exception as e:
        logger.error(f"Error generating PDF for application {application_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'application_id': application_id
        }


def process_application_submission(application_id):
    """
    Background task to process a complete application submission.
    This includes PDF generation only (email is sent immediately in the view).
    
    Args:
        application_id (int): ID of the application
    """
    try:
        application = SupplierApplication.objects.get(id=application_id)
        
        # Generate PDF only - email is sent immediately in the view
        pdf_result = generate_application_pdf_task(application_id)
        
        logger.info(f"Application submission processed for {application_id} (PDF only)")
        
        return {
            'success': True,
            'pdf_result': pdf_result,
            'application_id': application_id
        }
        
    except Exception as e:
        logger.error(f"Error processing application submission {application_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'application_id': application_id
        }