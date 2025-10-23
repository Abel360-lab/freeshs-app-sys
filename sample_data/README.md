# Import/Export Templates

This directory contains sample CSV and Excel templates for importing data into the GCX Supplier Portal system.

## Available Templates

### Supported File Formats
- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx) - Microsoft Excel 2007+
- **Excel Legacy** (.xls) - Microsoft Excel 97-2003

### 1. Regions
- `regions_import_template.csv` - CSV template
- `regions_import_template.xlsx` - Excel template

Import regions for the school system.

**Required Fields:**
- `name`: Region name (e.g., "Greater Accra Region")
- `code`: Region code (e.g., "GA")
- `is_active`: Boolean (True/False)

### 2. Commodities
- `commodities_import_template.csv` - CSV template
- `commodities_import_template.xlsx` - Excel template

Import commodities that can be supplied to schools.

**Required Fields:**
- `name`: Commodity name (e.g., "Rice")
- `description`: Description of the commodity
- `is_active`: Boolean (True/False)
- `is_processed_food`: Boolean (True/False)

### 3. Schools
- `schools_import_template.csv` - CSV template
- `schools_import_template.xlsx` - Excel template
- `ahafo_schools.xlsx` - Sample Ahafo region schools

Import schools with their details.

**Required Fields:**
- `name`: School name
- `code`: Unique school code
- `Region`: Region name (must match existing region)
- `district`: District name
- `address`: School address

**Optional Fields:**
- `contact_person`: Contact person name
- `contact_phone`: Contact phone number
- `contact_email`: Contact email address
- `is_active`: Boolean (True/False)

## How to Use Import/Export

### Method 1: Using Management Command (Recommended)

The easiest way to import sample data is using the management command:

```bash
# Import all sample data (regions, commodities, schools)
python manage.py import_sample_data

# Import specific data types
python manage.py import_sample_data --regions
python manage.py import_sample_data --commodities  
python manage.py import_sample_data --schools

# Force reimport even if data exists
python manage.py import_sample_data --force

# Import from Excel files
python manage.py import_excel --file sample_data/schools_import_template.xlsx --type schools
python manage.py import_excel --file sample_data/regions_import_template.xlsx --type regions
python manage.py import_excel --file sample_data/commodities_import_template.xlsx --type commodities

# Import with specific sheet (for multi-sheet Excel files)
python manage.py import_excel --file data.xlsx --type schools --sheet 0
```

### Method 2: Using Django Admin

1. **Navigate to the model** you want to import/export (e.g., `/admin/applications/school/`)

2. **Export Data:**
   - Click the "Export" button
   - Select format (CSV, XLSX, XLS, JSON)
   - Choose fields to export
   - Click "Submit"

3. **Import Data:**
   - Click the "Import" button
   - Upload your CSV or Excel file (.csv, .xlsx, .xls)
   - Review the preview
   - Click "Confirm import"

### Import Process:

1. **Prepare your CSV or Excel file** using the templates provided
2. **Ensure data consistency:**
   - Region names must match existing regions
   - School codes must be unique
   - Boolean fields should be "True" or "False"
   - For Excel files, use the first sheet or specify sheet number
3. **Upload the file** through the admin interface or use management commands
4. **Review the preview** to check for errors
5. **Confirm the import** to add the data

### Export Process:

1. **Navigate to the model** in admin
2. **Click "Export"**
3. **Select format and fields**
4. **Download the file**

## Important Notes

- **Contact information is optional** for schools
- **Region names must exist** before importing schools
- **School codes must be unique**
- **Boolean fields** should use "True" or "False"
- **Dates** should be in YYYY-MM-DD format
- **File encoding** should be UTF-8

## Troubleshooting

### Common Import Errors:

1. **"'NoneType' object has no attribute 'name'"**
   - This error occurs when regions don't exist in the database
   - **Solution**: Import regions first using the management command:
     ```bash
     python manage.py import_sample_data --regions
     ```
   - Or ensure region names in your CSV match existing regions exactly

2. **"Region does not exist"**
   - Import regions first before importing schools
   - Check region name spelling (must match exactly, e.g., "Greater Accra Region")
   - Use the management command to import in correct order

3. **"Duplicate school code"**
   - Ensure school codes are unique
   - Check existing data for duplicates

4. **"Invalid boolean value"**
   - Use "True" or "False" (case-sensitive)
   - Don't use "1", "0", "yes", "no"

5. **"Invalid date format"**
   - Use YYYY-MM-DD format
   - Example: 2024-01-15

### File Format Requirements:

- **CSV files** should use comma separators
- **Excel files** (.xlsx/.xls) are fully supported
- **UTF-8 encoding** is recommended for CSV files
- **First row** should contain column headers
- **No empty rows** between data
- **Excel multi-sheet support** - specify sheet number if needed

## Sample Data

The templates include sample data from various regions in Ghana:
- Greater Accra
- Ashanti
- Northern
- Central
- Volta
- And more...

You can modify these templates to add your own data or use them as examples for creating your own import files.
