"""
Enhanced PDF generation service for supplier applications.
Designed to match professional GCX application format with modern styling.
"""

import os
import hashlib
from datetime import datetime
from io import BytesIO
import qrcode

from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, KeepTogether, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class EnhancedApplicationPDFService:
    """
    Enhanced service for generating professional PDF documents matching GCX style.
    Features:
    - Professional header with logo
    - Passport photos embedded in sections
    - QR code for document verification
    - Document hash for authenticity
    - Signatures with images
    - Comprehensive document status table
    - Modern table styling
    """
    
    def __init__(self):
        self.page_size = A4
        self.margin = 0.5 * inch
        self.styles = self._create_custom_styles()
        self.page_width = A4[0] - 2 * self.margin
    
    def _create_custom_styles(self):
        """Create custom paragraph styles matching the GCX document format."""
        styles = getSampleStyleSheet()
        
        custom_styles = {
            'main_title': ParagraphStyle(
                'MainTitle',
                parent=styles['Heading1'],
                fontSize=18,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                textColor=colors.black,
                spaceAfter=4,
                spaceBefore=0
            ),
            
            'sub_title': ParagraphStyle(
                'SubTitle',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica',
                alignment=TA_CENTER,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0
            ),
            
            'section_title': ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=11,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                textColor=colors.black,
                backgroundColor=colors.Color(0.96, 0.96, 0.96),  # #f5f5f5 (same as table header)
                spaceAfter=10,
                spaceBefore=10,
                leftIndent=5,
                rightIndent=5,
                leading=16
            ),
            
            'label': ParagraphStyle(
                'Label',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                textColor=colors.black,
                spaceAfter=0,
                spaceBefore=0
            ),
            
            'value': ParagraphStyle(
                'Value',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica',
                alignment=TA_LEFT,
                textColor=colors.black,
                spaceAfter=0,
                spaceBefore=0
            ),
            
            'footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica',
                alignment=TA_CENTER,
                textColor=colors.Color(0.4, 0.4, 0.4),  # #666666
                spaceAfter=0,
                spaceBefore=5
            ),
            
            'pending_doc': ParagraphStyle(
                'PendingDoc',
                parent=styles['Normal'],
                fontSize=9,
                fontName='Helvetica',
                alignment=TA_LEFT,
                textColor=colors.Color(0.52, 0.39, 0.02),  # #856404
                backgroundColor=colors.Color(1.0, 0.95, 0.80),  # #fff3cd
                leftIndent=6,
                borderColor=colors.Color(1.0, 0.76, 0.03),  # #ffc107
                borderWidth=3,
                borderPadding=3,
                spaceAfter=3
            ),
            
            'table_header': ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=9,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                textColor=colors.black
            ),
            
            'table_cell': ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=9,
                fontName='Helvetica',
                alignment=TA_LEFT,
                textColor=colors.black
            ),
        }
        
        return custom_styles
    
    def _generate_document_hash(self, application):
        """Generate SHA-256 hash for document verification."""
        hash_string = f"{application.id}{application.tracking_code}{application.created_at}{settings.SECRET_KEY}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _generate_qr_code(self, application):
        """Generate QR code for document verification."""
        try:
            document_hash = self._generate_document_hash(application)
            
            # Update application with verification hash (if field exists)
            if hasattr(application, 'verification_hash'):
                application.verification_hash = document_hash
                application.save(update_fields=['verification_hash'])
            
            # Generate verification URL
            base_url = getattr(settings, 'SITE_URL', 'https://gcx.com.gh')
            verification_url = f"{base_url}/verify-document/?id={application.id}&hash={document_hash}"
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=2,
                border=1,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Generate QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to ReportLab Image
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_image = RLImage(buffer, width=1.5*inch, height=1.5*inch)
            return qr_image, document_hash
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None, None
    
    def _get_image_as_reportlab(self, file_field, max_width=120, max_height=150):
        """Convert a Django FileField image to ReportLab Image."""
        try:
            if not file_field:
                return None
            
            # Open image
            img_path = file_field.path if hasattr(file_field, 'path') else str(file_field)
            
            if not os.path.exists(img_path):
                return None
            
            # Open with PIL to get dimensions
            pil_img = Image.open(img_path)
            width, height = pil_img.size
            
            # Calculate aspect ratio
            aspect = width / height
            
            # Resize to fit max dimensions
            if width > max_width or height > max_height:
                if aspect > 1:  # Wider than tall
                    new_width = max_width
                    new_height = max_width / aspect
                else:  # Taller than wide
                    new_height = max_height
                    new_width = max_height * aspect
            else:
                new_width = width
                new_height = height
            
            # Create ReportLab Image
            rl_img = RLImage(img_path, width=new_width, height=new_height)
            return rl_img
            
        except Exception as e:
            logger.warning(f"Could not load image: {e}")
            return None
    
    def _add_header(self, story, application):
        """Add professional header section with logo."""
        # Create header table with logo and title
        header_data = []
        
        # Try to get logo
        logo_path = os.path.join(settings.MEDIA_ROOT, 'logo', 'logo1.png')
        logo_img = None
        
        if os.path.exists(logo_path):
            try:
                logo_img = RLImage(logo_path, width=100, height=60)
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")
        
        # Build header content
        title_parts = [
            Paragraph("SUPPLIER APPLICATION FORM", self.styles['main_title']),
            Spacer(1, 4),
            Paragraph(f"<b>Application Reference:</b> {application.tracking_code}", self.styles['sub_title']),
            Paragraph(f"<b>Status:</b> {application.get_status_display()}", self.styles['sub_title']),
            Paragraph(f"<b>Date Submitted:</b> {application.created_at.strftime('%d %B %Y')}", 
                     self.styles['sub_title']),
        ]
        
        if logo_img:
            # Logo on left, title on right
            header_data = [[logo_img, title_parts]]
            header_table = Table(header_data, colWidths=[1.2*inch, self.page_width - 1.2*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(header_table)
        else:
            # Just title
            for part in title_parts:
                story.append(part)
        
        # Add horizontal line
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        story.append(Spacer(1, 15))
    
    def _create_section_with_photo(self, title, data, photo_field=None, photo_label=""):
        """Create a section with optional photo on the right side."""
        elements = []
        
        # Section title
        elements.append(Paragraph(title, self.styles['section_title']))
        elements.append(Spacer(1, 5))
        
        # Get photo if provided
        photo_img = None
        if photo_field:
            photo_img = self._get_image_as_reportlab(photo_field, max_width=100, max_height=120)
        
        # Create main content table
        content_data = []
        for label, value in data:
            content_data.append([
                Paragraph(f"<b>{label}</b>", self.styles['label']),
                Paragraph(str(value), self.styles['value'])
            ])
        
        if photo_img:
            # Create layout with photo on the side
            content_table = Table(content_data, colWidths=[2*inch, 3*inch])
            content_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            # Photo cell
            photo_cell = [
                photo_img,
                Spacer(1, 5),
                Paragraph(f"<b>{photo_label}</b>", self.styles['table_cell'])
            ]
            
            # Combine content and photo
            combined_data = [[content_table, photo_cell]]
            combined_table = Table(combined_data, colWidths=[5*inch, 1.6*inch])
            combined_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(combined_table)
        else:
            # Just content without photo
            content_table = Table(content_data, colWidths=[2*inch, 4.6*inch])
            content_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(content_table)
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_styled_table(self, data, col_widths=None, has_header=True):
        """Create a professionally styled table."""
        if col_widths is None:
            # Auto-calculate widths
            num_cols = len(data[0]) if data else 1
            col_widths = [self.page_width / num_cols] * num_cols
        
        table = Table(data, colWidths=col_widths)
        
        style_commands = [
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.87, 0.87, 0.87)),  # #dddddd
        ]
        
        if has_header:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.96, 0.96, 0.96)),  # #f5f5f5
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ])
        
        table.setStyle(TableStyle(style_commands))
        return table
    
    def _create_section_header(self, title):
        """Create a section header with background color using a table."""
        header_text = Paragraph(f"<b>{title}</b>", self.styles['label'])
        header_table = Table([[header_text]], colWidths=[self.page_width])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.96, 0.96, 0.96)),  # #f5f5f5
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return header_table
    
    def _add_company_details(self, story, application):
        """Add company details section."""
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("COMPANY DETAILS"))
        story.append(Spacer(1, 5))
        
        data = [
            ('Company Name:', application.business_name),
            ('Business Type:', application.get_business_type_display()),
            ('Registration Number:', application.registration_number or 'Not Provided'),
            ('TIN Number:', application.tin_number or 'Not Provided'),
            ('Place of Business:', application.physical_address),
            ('City:', application.city),
            ('Region:', application.region.name if application.region else 'Not Specified'),
            ('Country:', application.country),
            ('Telephone:', application.telephone),
            ('Email:', application.email),
            ('Warehouse Location:', application.warehouse_location),
        ]
        
        content_data = []
        for label, value in data:
            content_data.append([
                Paragraph(f"<b>{label}</b>", self.styles['label']),
                Paragraph(str(value), self.styles['value'])
            ])
        
        content_table = Table(content_data, colWidths=[2*inch, 4.6*inch])
        content_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(content_table)
        story.append(Spacer(1, 15))
    
    def _add_commodities_section(self, story, application):
        """Add commodities section."""
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("COMMODITIES TO SUPPLY"))
        story.append(Spacer(1, 5))
        
        # Get selected commodities
        commodities_selected = list(application.commodities_to_supply.all())
        
        if commodities_selected:
            # Display as styled badges/chips
            commodity_data = []
            row = []
            for i, commodity in enumerate(commodities_selected):
                row.append(Paragraph(f"☑ {commodity.name}", self.styles['value']))
                
                if (i + 1) % 3 == 0:
                    commodity_data.append(row)
                    row = []
            
            # Add remaining items
            if row:
                while len(row) < 3:
                        row.append('')
                commodity_data.append(row)
            
            commodity_table = Table(commodity_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
            commodity_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(commodity_table)
        else:
            story.append(Paragraph("☐ No commodities selected", self.styles['value']))
        
        # Other commodities
        if application.other_commodities:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Additional Commodities:</b>", self.styles['label']))
            story.append(Paragraph(application.other_commodities, self.styles['value']))
        
        story.append(Spacer(1, 15))
    
    def _add_next_of_kin(self, story, application):
        """Add next of kin details section."""
        if not application.next_of_kin.exists():
            return
        
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("NEXT OF KIN DETAILS"))
        story.append(Spacer(1, 5))
        
        for i, kin in enumerate(application.next_of_kin.all()):
            if i > 0:
                story.append(Spacer(1, 10))
            
            kin_data = [
                ('Full Name:', kin.full_name),
                ('Relationship:', kin.relationship),
                ('Address:', kin.address),
                ('Mobile:', kin.mobile),
                ('Email:', getattr(kin, 'email', 'Not Provided')),
                ('ID Type:', kin.get_id_card_type_display()),
                ('ID Number:', kin.id_card_number),
            ]
            
            content_data = []
            for label, value in kin_data:
                content_data.append([
                    Paragraph(f"<b>{label}</b>", self.styles['label']),
                    Paragraph(str(value), self.styles['value'])
                ])
            
            content_table = Table(content_data, colWidths=[2*inch, 4.6*inch])
            content_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(content_table)
        
        story.append(Spacer(1, 15))
    
    def _add_team_members(self, story, application):
        """Add team members/contact persons section."""
        if not application.team_members.exists():
            return
        
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("CONTACT PERSONS / TEAM MEMBERS"))
        story.append(Spacer(1, 5))
        
        for i, member in enumerate(application.team_members.all()):
            if i > 0:
                story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>Contact Person {i + 1}</b>", self.styles['label']))
            story.append(Spacer(1, 3))
            
            # Get photo if available
            photo_field = getattr(member, 'passport_photo', None) or getattr(member, 'id_card', None)
            
            member_data = [
                ('Full Name:', member.full_name),
                ('Position:', member.position or 'Team member'),
                ('Email:', member.email),
                ('Telephone:', member.telephone),
                ('Residential Address:', member.address),
                ('Years of Experience:', f"{member.years_experience} years" if member.years_experience else 'N/A'),
                ('ID Type:', member.get_id_card_type_display()),
                ('ID Number:', member.id_card_number),
            ]
            
            elements = self._create_section_with_photo(
                "",  # No title, already added above
                member_data,
                photo_field=photo_field,
                photo_label="Contact Person Photo"
            )
            
            # Skip the first element (section title) since we already added it
            for elem in elements[2:]:  # Skip title and first spacer
                story.append(elem)
        
        story.append(Spacer(1, 15))
    
    def _add_bank_details(self, story, application):
        """Add bank account details section."""
        if not application.bank_accounts.exists():
            return
        
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("BANK ACCOUNT DETAILS"))
        story.append(Spacer(1, 5))
        
        for i, account in enumerate(application.bank_accounts.all()):
            if i > 0:
                story.append(Spacer(1, 10))
            
            account_data = [
                ('Bank Name:', account.bank_name),
                ('Branch:', account.branch),
                ('Account Name:', account.account_name),
                ('Account Number:', account.account_number),
            ]
            
            content_data = []
            for label, value in account_data:
                content_data.append([
                    Paragraph(f"<b>{label}</b>", self.styles['label']),
                    Paragraph(str(value), self.styles['value'])
                ])
            
            content_table = Table(content_data, colWidths=[2*inch, 4.6*inch])
            content_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(content_table)
        
        story.append(Spacer(1, 15))
    
    def _add_uploaded_documents(self, story, application):
        """Add uploaded documents section with status."""
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("UPLOADED DOCUMENTS"))
        story.append(Spacer(1, 5))
        
        logger.info(f"Checking uploaded documents for application {application.tracking_code}")
        
        # Document folder mapping (documents are stored in media/documents/{tracking_code}/{FOLDER_NAME}/)
        document_folders = {
            'BUSINESS_REGISTRATION_DOCS': 'Business Registration Certificate',
            'VAT_CERTIFICATE': 'VAT Certificate',
            'PPA_CERTIFICATE': 'PPA Certificate',
            'TAX_CLEARANCE_CERT': 'Tax Clearance Certificate',
            'PROOF_OF_OFFICE': 'Proof of Office',
            'ID_MD_CEO_PARTNERS': 'ID Cards of Directors',
            'GCX_REGISTRATION_PROOF': 'GCX Registration Documents',
            'TEAM_MEMBER_ID': 'Team Member ID Documents',
            'FDA_CERT_PROCESSED_FOOD': 'FDA Certificate',
        }
        
        table_data = [
            [
                Paragraph('<b>Document Type</b>', self.styles['table_header']),
                Paragraph('<b>Status</b>', self.styles['table_header']),
                Paragraph('<b>Upload Date</b>', self.styles['table_header']),
            ]
        ]
        
        # Build path to application documents folder
        docs_base_path = os.path.join(settings.MEDIA_ROOT, 'documents', application.tracking_code)
        logger.debug(f"  Documents path: {docs_base_path}")
        
        for folder_name, label in document_folders.items():
            # Check if document folder exists and has files
            is_submitted = False
            date_str = '-'
            file_count = 0
            
            folder_path = os.path.join(docs_base_path, folder_name)
            
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Count files in the folder (excluding directories)
                files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                file_count = len(files)
                
                if file_count > 0:
                    is_submitted = True
                    logger.debug(f"  ✓ {folder_name}: {file_count} file(s)")
                    
                    # Get the most recent file's modification date
                    try:
                        file_paths = [os.path.join(folder_path, f) for f in files]
                        most_recent_file = max(file_paths, key=os.path.getmtime)
                        upload_date = datetime.fromtimestamp(os.path.getmtime(most_recent_file))
                        date_str = upload_date.strftime('%d/%m/%Y')
                    except Exception as e:
                        logger.warning(f"Could not get date for {folder_name}: {e}")
                        date_str = 'Uploaded'
                else:
                    logger.debug(f"  ✗ {folder_name}: Folder exists but empty")
            else:
                logger.debug(f"  ✗ {folder_name}: Folder does not exist")
            
            # Set status based on submission
            if is_submitted:
                status = '<font color="#155724">✓ Submitted</font>'
            else:
                status = '<font color="#721c24">✗ Not Submitted</font>'
            
            table_data.append([
                Paragraph(label, self.styles['table_cell']),
                Paragraph(status, self.styles['table_cell']),
                Paragraph(date_str, self.styles['table_cell']),
            ])
        
        doc_table = self._create_styled_table(
            table_data,
            col_widths=[3.5*inch, 1.8*inch, 1.3*inch],
            has_header=True
        )
        
        story.append(doc_table)
        story.append(Spacer(1, 15))
    
    def _add_declarations(self, story, application):
        """Add declarations and compliance section."""
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("ABIDANCE BY RULES AND REGULATIONS"))
        story.append(Spacer(1, 5))
        
        # Rules agreement
        agreement_status = '☑ Yes' if application.declaration_agreed else '☐ Yes'
        story.append(Paragraph(
            f"If accepted as a supplier, do you agree to abide by the Rules and Guidelines? <b>{agreement_status}</b>",
            self.styles['value']
        ))
        story.append(Spacer(1, 12))
        
        # Declaration text
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("DECLARATION"))
        story.append(Spacer(1, 5))
        
        declaration_text = """
        We hereby declare that the details furnished above are true and correct to the best of our 
        knowledge and belief and we undertake to inform you of any changes therein immediately. 
        In case any of the above information is found to be false or untrue or misleading or 
        misrepresenting we are aware that we may be held liable for it.
        <br/><br/>
        We undertake that any misstatement or misrepresentation or suppression of facts in 
        connection with this application for supplier registration or breach of any undertaking or condition 
        of admission may entail rejection of our application or removal from the supplier registry.
        """
        
        story.append(Paragraph(declaration_text, self.styles['value']))
        story.append(Spacer(1, 15))
        
        # Signature section
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("SIGNATURE"))
        story.append(Spacer(1, 5))
        
        signature_data = [
            ('Name:', application.signer_name or 'Not Provided'),
            ('Designation:', application.signer_designation or 'Not Provided'),
            ('Date:', application.signed_at.strftime('%d %B %Y') if application.signed_at else 'Not Signed'),
        ]
        
        content_data = []
        for label, value in signature_data:
            content_data.append([
                Paragraph(f"<b>{label}</b>", self.styles['label']),
                Paragraph(str(value), self.styles['value'])
            ])
        
        signature_table = Table(content_data, colWidths=[2*inch, 4.6*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.Color(0.87, 0.87, 0.87)),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 20))
    
    def _add_verification_section(self, story, application):
        """Add QR code and verification section."""
        story.append(Spacer(1, 10))
        story.append(self._create_section_header("DOCUMENT VERIFICATION"))
        story.append(Spacer(1, 8))
        
        # Generate QR code
        qr_image, document_hash = self._generate_qr_code(application)
        
        if qr_image:
            # Center the QR code
            qr_table = Table([[qr_image]], colWidths=[self.page_width])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ]))
            story.append(qr_table)
            
            story.append(Spacer(1, 5))
            story.append(Paragraph(
                "<b>Scan to verify document authenticity</b>",
                self.styles['footer']
            ))
            
            if document_hash:
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    f"Document Hash: {document_hash[:32]}...",
                    self.styles['footer']
                ))
        
        story.append(Spacer(1, 20))
    
    def _add_footer(self, story, application):
        """Add footer with generation details."""
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 8))
        
        footer_lines = [
            "This is a system-generated document from the GCX Supplier Application Portal",
            f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}",
            "",
            "Please submit completed form to:",
            "HEAD, Membership & Special Projects",
            "Ghana Commodity Exchange",
            "2nd Floor Africa Trade House | Cruickshank Road/Liberia Road | Ridge – Accra",
            "Phone: 0302 937 677 | Mobile: 0594164479/0594164473",
            "Email: membership@gcx.com.gh | Website: www.gcx.com.gh"
        ]
        
        for line in footer_lines:
            story.append(Paragraph(line, self.styles['footer']))
    
    def generate_application_pdf(self, application):
        """
        Generate a professional PDF matching the GCX application format.
        
        Args:
            application: SupplierApplication instance
            
        Returns:
            str: Path to the generated PDF file, or None if generation failed
        """
        try:
            logger.info(f"Generating enhanced PDF for application {application.tracking_code}")
            
            # Create a BytesIO buffer to hold the PDF
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
                title=f"Application - {application.tracking_code}"
            )
            
            # Build the PDF content
            story = []
            
            # Add all sections
            self._add_header(story, application)
            self._add_company_details(story, application)
            self._add_commodities_section(story, application)
            self._add_next_of_kin(story, application)
            self._add_team_members(story, application)
            self._add_bank_details(story, application)
            self._add_uploaded_documents(story, application)
            self._add_declarations(story, application)
            self._add_verification_section(story, application)
            self._add_footer(story, application)
            
            # Build PDF
            doc.build(story)
            
            # Get the PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Save the PDF to the application's pdf_file field
            filename = f"supplier_application_{application.tracking_code}.pdf"
            application.pdf_file.save(filename, ContentFile(pdf_content), save=True)
            
            logger.info(f"Successfully generated enhanced PDF for application {application.tracking_code}")
            return application.pdf_file.name
            
        except Exception as e:
            logger.error(f"Error generating enhanced PDF for application {application.tracking_code}: {e}", exc_info=True)
            return None


def generate_application_pdf_response(application):
    """Generate an enhanced PDF response for download."""
    try:
        pdf_service = EnhancedApplicationPDFService()
        pdf_path = pdf_service.generate_application_pdf(application)
        
        if pdf_path:
            from django.http import HttpResponse
            
            # Read the saved PDF file
            with open(application.pdf_file.path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="supplier_application_{application.tracking_code}.pdf"'
                return response
        else:
            raise Exception("PDF generation failed")
        
    except Exception as e:
        logger.error(f"Error generating PDF response for application {application.id}: {str(e)}")
        raise


# Backward compatibility - alias to the original class name
ApplicationPDFService = EnhancedApplicationPDFService
