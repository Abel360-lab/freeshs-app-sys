"""
PDF generation service for supplier applications using ReportLab.
"""

import os
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class ApplicationPDFService:
    """Service for generating PDF documents from application data using ReportLab."""
    
    def __init__(self):
        self.page_size = A4
        self.margin = 0.75 * inch
    
    def generate_application_pdf(self, application):
        """
        Generates a PDF of the application details and saves it to the application instance.
        
        Args:
            application: SupplierApplication instance
            
        Returns:
            str: Path to the generated PDF file, or None if generation failed
        """
        try:
            # Create a BytesIO buffer to hold the PDF
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Create custom styles for professional look
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=15,
                spaceBefore=25,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=colors.darkblue,
                borderPadding=10,
                backColor=colors.lightgrey
            )
            
            subheader_style = ParagraphStyle(
                'CustomSubHeader',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            # Build the PDF content
            story = []
            
            # Professional Header with Logo
            # Add logo if it exists
            logo_path = os.path.join(settings.MEDIA_ROOT, 'logo', 'logo1.png')
            if os.path.exists(logo_path):
                from reportlab.platypus import Image
                try:
                    # Add logo
                    logo = Image(logo_path, width=80, height=80)
                    story.append(logo)
                    story.append(Spacer(1, 15))
                except Exception as e:
                    logger.warning(f"Could not add logo to PDF: {e}")
            
            # Official Header
            story.append(Paragraph("GHANA COMMODITY EXCHANGE", 
                                 ParagraphStyle('OfficialTitle', parent=styles['Heading1'], 
                                               fontSize=20, alignment=TA_CENTER, 
                                               textColor=colors.darkblue, fontName='Helvetica-Bold')))
            story.append(Paragraph("SUPPLIER APPLICATION FORM", 
                                 ParagraphStyle('OfficialSubtitle', parent=styles['Heading2'], 
                                               fontSize=16, alignment=TA_CENTER, 
                                               textColor=colors.darkblue, fontName='Helvetica-Bold')))
            story.append(Spacer(1, 25))
            
            # Application Reference Section
            story.append(Paragraph("APPLICATION REFERENCE", header_style))
            
            ref_data = [
                ['Application Reference:', application.tracking_code],
                ['Application Date:', application.created_at.strftime('%B %d, %Y at %I:%M %p')],
                ['Current Status:', application.get_status_display()],
                ['Business Name:', application.business_name],
            ]
            
            ref_table = Table(ref_data, colWidths=[2.5*inch, 4*inch])
            ref_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(ref_table)
            story.append(Spacer(1, 25))
            
            # Business Information Section
            story.append(Paragraph("COMPANY INFORMATION", header_style))
            
            business_data = [
                ['Company Name:', application.business_name],
                ['Business Type:', application.get_business_type_display()],
                ['Registration Number:', application.registration_number or 'Not Provided'],
                ['Tax Identification Number:', application.tin_number or 'Not Provided'],
                ['Physical Address:', application.physical_address],
                ['City:', application.city],
                ['Region:', application.region.name if application.region else 'Not Specified'],
                ['Contact Phone:', application.telephone],
                ['Email Address:', application.email],
                ['Warehouse Location:', application.warehouse_location],
            ]
            
            business_table = Table(business_data, colWidths=[2.5*inch, 4*inch])
            business_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Bold for labels
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),       # Regular for values
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(business_table)
            story.append(Spacer(1, 25))
            
            # Commodities Section
            story.append(Paragraph("COMMODITIES TO SUPPLY", header_style))
            
            commodities_text = []
            if application.commodities_to_supply.exists():
                commodities_text.append("<b>Predefined Commodities:</b>")
                for commodity in application.commodities_to_supply.all():
                    commodities_text.append(f"• {commodity.name}")
            
            if application.other_commodities:
                commodities_text.append("<b>Other Commodities:</b>")
                commodities_text.append(f"• {application.other_commodities}")
            
            if not commodities_text:
                commodities_text.append("No commodities specified")
            
            story.append(Paragraph("<br/>".join(commodities_text), normal_style))
            story.append(Spacer(1, 25))
            
            # Documents Section
            story.append(Paragraph("REQUIRED DOCUMENTS STATUS", header_style))
            
            # Get document uploads from DocumentUpload model
            from documents.models import DocumentUpload, DocumentRequirement
            
            # Get all document requirements
            doc_requirements = DocumentRequirement.objects.filter(is_active=True)
            
            # Get all uploads for this application
            doc_uploads = DocumentUpload.objects.filter(application=application)
            
            doc_data = [['Document Type', 'Status']]
            for req in doc_requirements:
                upload = doc_uploads.filter(requirement=req).first()
                status = '✓ SUBMITTED' if upload else '✗ PENDING'
                doc_data.append([req.label, status])
            
            doc_table = Table(doc_data, colWidths=[3.5*inch, 2*inch])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(doc_table)
            story.append(Spacer(1, 25))
            
            story.append(Spacer(1, 25))
            
            # Team Members Section
            if application.team_members.exists():
                story.append(Paragraph("KEY PERSONNEL", header_style))
                
                for i, member in enumerate(application.team_members.all(), 1):
                    story.append(Paragraph(f"Personnel {i}", subheader_style))
                    
                    member_data = [
                        ['Full Name:', member.full_name],
                        ['Position:', member.position or 'N/A'],
                        ['Years of Experience:', f"{member.years_experience} years" if member.years_experience else 'N/A'],
                        ['Address:', member.address],
                        ['City:', member.city],
                        ['Region:', member.region.name if member.region else 'N/A'],
                        ['Phone:', member.telephone],
                        ['Email:', member.email],
                        ['ID Type:', member.get_id_card_type_display()],
                        ['ID Number:', member.id_card_number],
                    ]
                    
                    member_table = Table(member_data, colWidths=[2.5*inch, 4*inch])
                    member_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('BACKGROUND', (1, 0), (1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    story.append(member_table)
                    story.append(Spacer(1, 15))
                
                story.append(Spacer(1, 20))
            
            # Next of Kin Section
            if application.next_of_kin.exists():
                story.append(Paragraph("NEXT OF KIN", header_style))
                
                for i, kin in enumerate(application.next_of_kin.all(), 1):
                    story.append(Paragraph(f"Contact {i}", subheader_style))
                    
                    kin_data = [
                        ['Full Name:', kin.full_name],
                        ['Relationship:', kin.relationship],
                        ['Address:', kin.address],
                        ['Mobile:', kin.mobile],
                        ['ID Type:', kin.get_id_card_type_display()],
                        ['ID Number:', kin.id_card_number],
                    ]
                    
                    kin_table = Table(kin_data, colWidths=[2.5*inch, 4*inch])
                    kin_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('BACKGROUND', (1, 0), (1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    story.append(kin_table)
                    story.append(Spacer(1, 15))
                
                story.append(Spacer(1, 20))
            
            # Bank Accounts Section
            if application.bank_accounts.exists():
                story.append(Paragraph("BANKING INFORMATION", header_style))
                
                for i, account in enumerate(application.bank_accounts.all(), 1):
                    story.append(Paragraph(f"Account {i}", subheader_style))
                    
                    account_data = [
                        ['Bank Name:', account.bank_name],
                        ['Account Name:', account.account_name],
                        ['Account Number:', account.account_number],
                        ['Branch:', account.branch],
                        ['Account Type:', f"Option {account.account_index}"],
                    ]
                    
                    account_table = Table(account_data, colWidths=[2.5*inch, 4*inch])
                    account_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('BACKGROUND', (1, 0), (1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    story.append(account_table)
                    story.append(Spacer(1, 15))
                
                story.append(Spacer(1, 20))
            
            # Application Timeline Section
            story.append(Paragraph("APPLICATION TIMELINE", header_style))
            
            timeline_data = [
                ['Application Submitted:', application.submitted_at.strftime('%B %d, %Y at %I:%M %p') if application.submitted_at else 'Not Available'],
                ['Application Reviewed:', application.reviewed_at.strftime('%B %d, %Y at %I:%M %p') if application.reviewed_at else 'Pending Review'],
                ['Decision Made:', application.decided_at.strftime('%B %d, %Y at %I:%M %p') if application.decided_at else 'Pending Decision'],
                ['Data Consent Given:', 'Yes' if application.data_consent else 'No'],
            ]
            
            timeline_table = Table(timeline_data, colWidths=[2.5*inch, 4*inch])
            timeline_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(timeline_table)
            story.append(Spacer(1, 25))
            
            # Declaration Section
            story.append(Paragraph("DECLARATION", header_style))
            
            declaration_text = """
            I hereby declare that the information provided in this application is true and accurate to the best of my knowledge. 
            I understand that any false information may result in the rejection of my application.
            """
            
            story.append(Paragraph(declaration_text, normal_style))
            story.append(Spacer(1, 10))
            
            # Declaration status
            if application.declaration_agreed:
                story.append(Paragraph("✓ Declaration agreed to", normal_style))
            else:
                story.append(Paragraph("✗ Declaration not agreed to", normal_style))
            
            # Signer information
            if application.signer_name:
                story.append(Spacer(1, 15))
                story.append(Paragraph(f"Signed by: {application.signer_name}", normal_style))
                if application.signer_designation:
                    story.append(Paragraph(f"Designation: {application.signer_designation}", normal_style))
                if application.signed_at:
                    story.append(Paragraph(f"Date: {application.signed_at.strftime('%B %d, %Y at %I:%M %p')}", normal_style))
            
            # Add footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Generated on: {application.created_at.strftime('%B %d, %Y at %I:%M %p')}", 
                                 ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                               alignment=TA_CENTER, textColor=colors.grey)))
            
            # Build PDF
            doc.build(story)
            
            # Get the PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Save the PDF to the application's pdf_file field
            filename = f"application_{application.tracking_code}.pdf"
            application.pdf_file.save(filename, ContentFile(pdf_content), save=True)
            
            logger.info(f"Successfully generated and saved PDF for application {application.tracking_code}")
            return application.pdf_file.name
            
        except Exception as e:
            logger.error(f"Error generating PDF for application {application.tracking_code}: {e}")
            return None


def generate_application_pdf_response(application):
    """Generate a PDF response for download."""
    try:
        pdf_service = ApplicationPDFService()
        pdf_content = pdf_service.generate_application_pdf(application)
        
        from django.http import HttpResponse
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="application_{application.tracking_code}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF response for application {application.id}: {str(e)}")
        raise
