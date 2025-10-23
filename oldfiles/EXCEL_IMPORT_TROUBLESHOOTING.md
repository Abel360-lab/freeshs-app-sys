# Excel Import Troubleshooting Guide

This guide helps resolve common issues when importing schools from Excel files.

## Common Error: 'NoneType' object has no attribute 'name'

### What This Error Means
This error occurs when the import process tries to access the `name` attribute of a `None` object, typically when:
- The region field is empty or null
- Column names don't match expected format
- Data is not properly formatted

### How to Fix

#### 1. Check Your Excel File Format

Ensure your Excel file has the correct column headers:

**Required Columns:**
- `Name` or `name`
- `Code` or `code` 
- `Region Name` or `region_name`
- `District` or `district`
- `Address` or `address`

**Optional Columns:**
- `ID` or `id`
- `Contact Person` or `contact_person`
- `Contact Phone` or `contact_phone`
- `Contact Email` or `contact_email`
- `Is Active` or `is_active`

#### 2. Use the Provided Template

Download and use the Excel template: `media/schools_import_template.xlsx`

This template has:
- Correct column headers
- Sample data
- Proper formatting

#### 3. Check Your Data

**Region Name Issues:**
- Ensure region names are not empty
- Use exact region names (case-insensitive)
- Common regions: "Ahafo Region", "Greater Accra", "Ashanti", "Volta", etc.

**Required Fields:**
- School Name: Cannot be empty
- School Code: Must be unique, cannot be empty
- District: Cannot be empty
- Address: Cannot be empty

#### 4. Excel Formatting Tips

**Avoid These Issues:**
- Empty rows between data
- Merged cells
- Special characters in headers
- Formulas in data cells
- Hidden rows or columns

**Best Practices:**
- Use plain text format
- No leading/trailing spaces
- Consistent date formats
- Boolean values as "True"/"False" or "1"/"0"

### Step-by-Step Solution

1. **Download Template:**
   ```
   Download: media/schools_import_template.xlsx
   ```

2. **Copy Your Data:**
   - Open the template
   - Copy your school data
   - Paste into the template
   - Ensure all required fields are filled

3. **Verify Format:**
   - Check that column headers match exactly
   - Ensure no empty required fields
   - Verify region names exist in the system

4. **Test Import:**
   - Try importing a small batch first
   - Check for error messages
   - Fix any issues before importing larger files

### Example Correct Format

| ID | Name | Code | Region Name | District | Address | Contact Person | Contact Phone | Contact Email | Is Active |
|----|------|------|-------------|----------|---------|----------------|---------------|---------------|-----------|
|    | SAMUEL OTU PRESBY SENIOR HIGH SCHOOL | SCH001 | Ahafo Region | Asunafo North | Full Address Here | John Doe | +233123456789 | contact@school.edu.gh | True |

### Debug Information

The system now provides debug output during import. Check the Django console/logs for:
```
Processing row: {'Name': 'School Name', 'Code': 'SCH001', ...}
```

This helps identify exactly what data is being processed.

### Still Having Issues?

If you continue to have problems:

1. **Check Django Logs:** Look for detailed error messages in the console
2. **Verify Data:** Ensure all required fields are populated
3. **Use CSV Instead:** Try converting your Excel file to CSV format
4. **Contact Support:** Provide the error message and a sample of your data

### Quick Fix Checklist

- [ ] Using correct column headers
- [ ] All required fields filled
- [ ] Region names match existing regions
- [ ] No empty rows in data
- [ ] School codes are unique
- [ ] File saved as Excel (.xlsx) format

### Alternative: Use CSV Format

If Excel continues to cause issues, you can:
1. Save your Excel file as CSV
2. Use the CSV import functionality
3. CSV format is often more reliable for imports

The CSV template is available at: `media/schools_import_template.csv`
