#!/usr/bin/env python
"""
Quick script to verify that commodities are correctly displayed in the generated PDF.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freeshs_app_sys.settings')
django.setup()

from applications.models import SupplierApplication
from applications.pdf_service import EnhancedApplicationPDFService

def verify_commodities():
    """Verify that commodities are correctly shown in the PDF."""
    print("🔍 Verifying commodities in PDF...")
    
    # Get the latest application
    application = SupplierApplication.objects.first()
    if not application:
        print("❌ No applications found")
        return
    
    print(f"📄 Application: {application.tracking_code}")
    print(f"🏢 Company: {application.business_name}")
    
    # Get selected commodities
    selected_commodities = [c.name for c in application.commodities_to_supply.all()]
    print(f"🌾 Selected commodities: {selected_commodities}")
    
    if not selected_commodities:
        print("⚠️ No commodities selected for this application")
        return
    
    # Generate PDF
    print("🔄 Generating PDF...")
    pdf_service = EnhancedApplicationPDFService()
    pdf_path = pdf_service.generate_application_pdf(application)
    
    if pdf_path and application.pdf_file:
        file_path = application.pdf_file.path
        print(f"✅ PDF generated: {file_path}")
        
        # Read PDF content
        try:
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            
            # Convert to text (basic extraction)
            pdf_text = pdf_content.decode('latin-1', errors='ignore')
            
            print("\n📋 Checking for commodities in PDF:")
            found_commodities = []
            missing_commodities = []
            
            for commodity in selected_commodities:
                if commodity in pdf_text:
                    found_commodities.append(commodity)
                    print(f"  ✅ Found: {commodity}")
                else:
                    missing_commodities.append(commodity)
                    print(f"  ❌ Missing: {commodity}")
            
            print(f"\n📊 Results:")
            print(f"  Found: {len(found_commodities)}/{len(selected_commodities)} commodities")
            print(f"  Success rate: {(len(found_commodities)/len(selected_commodities)*100):.1f}%")
            
            if found_commodities:
                print(f"\n✅ Commodities successfully included in PDF:")
                for commodity in found_commodities:
                    print(f"    - {commodity}")
            
            if missing_commodities:
                print(f"\n⚠️ Commodities not found in PDF:")
                for commodity in missing_commodities:
                    print(f"    - {commodity}")
            
            # Check for checkbox symbols
            if '☑' in pdf_text:
                print(f"\n✅ Found checkmark symbols (☑) in PDF")
            else:
                print(f"\n⚠️ No checkmark symbols found in PDF")
                
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
    else:
        print("❌ PDF generation failed")

if __name__ == "__main__":
    verify_commodities()
