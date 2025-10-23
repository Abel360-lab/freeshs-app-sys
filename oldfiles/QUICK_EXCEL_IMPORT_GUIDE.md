# Quick Excel Import Guide

## Fixed Issues ✅

The Excel import error has been resolved! The system now properly handles:
- Variable column names (Name, name, etc.)
- Null value protection
- Region auto-creation
- Better error messages

## How to Import Your Excel File

### Step 1: Prepare Your Excel File
Ensure your Excel file has these column headers (case-insensitive):
- **Name** - School name (required)
- **Code** - Unique school code (required)  
- **Region Name** - Region name (required)
- **District** - District name (required)
- **Address** - School address (required)
- **Contact Person** - Contact person (optional)
- **Contact Phone** - Phone number (optional)
- **Contact Email** - Email address (optional)
- **Is Active** - True/False (optional)

### Step 2: Use the Template (Recommended)
1. Download: `media/schools_import_template.xlsx`
2. Copy your data into the template
3. Ensure all required fields are filled
4. Save the file

### Step 3: Import Through Django Admin
1. Go to Django Admin → APPLICATIONS → Schools
2. Click "Import" button
3. Choose your Excel file
4. Review the import preview
5. Click "Submit" to import

## Example Excel Format

| Name | Code | Region Name | District | Address | Contact Person | Contact Phone | Contact Email | Is Active |
|------|------|-------------|----------|---------|----------------|---------------|---------------|-----------|
| SAMUEL OTU PRESBY SENIOR HIGH SCHOOL | SCH001 | Ahafo Region | Asunafo North | Full Address | John Doe | +233123456789 | contact@school.edu.gh | True |
| BECHEM PRESBY SENIOR HIGH SCHOOL | SCH002 | Ahafo Region | Asunafo South | Full Address | Jane Smith | +233987654321 | contact@school.edu.gh | True |

## Common Issues Fixed ✅

1. **'NoneType' object has no attribute 'name'** - FIXED
2. **'cannot access local variable 'code'** - FIXED  
3. **Region lookup errors** - FIXED
4. **Column name variations** - FIXED

## If You Still Have Issues

1. **Check Required Fields**: Ensure Name, Code, Region Name, District, and Address are not empty
2. **Use Template**: Download and use the provided Excel template
3. **Check Region Names**: Use exact region names like "Ahafo Region", "Greater Accra", etc.
4. **Try CSV**: Convert your Excel to CSV and import that instead

## Support Files Available

- **Excel Template**: `media/schools_import_template.xlsx`
- **CSV Template**: `media/schools_import_template.csv`
- **Detailed Guide**: `SCHOOL_IMPORT_EXPORT_GUIDE.md`
- **Troubleshooting**: `EXCEL_IMPORT_TROUBLESHOOTING.md`

The import functionality should now work correctly with your Excel files!
