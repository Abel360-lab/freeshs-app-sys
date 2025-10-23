# School Import/Export Guide

This guide explains how to use the import and export functionality for schools in the Django admin interface.

## Overview

The School model now supports importing and exporting data in CSV format. This allows administrators to:

- Export existing school data to CSV files
- Import new schools from CSV files
- Update existing schools using CSV files
- Bulk manage school data efficiently

## Features

### Export Functionality
- Export all schools or filtered schools to CSV
- Include region names instead of region IDs for readability
- Maintain data integrity and relationships
- Support for Excel-compatible CSV format

### Import Functionality
- Import schools from CSV files
- Update existing schools based on school code
- Automatic region creation if region doesn't exist
- Data validation and error reporting
- Skip unchanged records for efficiency

## CSV Format

The CSV file should have the following columns:

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| ID | School ID (leave empty for new schools) | No | 1 |
| Name | School name | Yes | SAMUEL OTU PRESBY SENIOR HIGH SCHOOL |
| Code | Unique school code | Yes | SCH001 |
| Region Name | Name of the region | Yes | Ahafo Region |
| District | District name | Yes | Asunafo North |
| Address | School address | Yes | SAMUEL OTU PRESBY SENIOR HIGH SCHOOL - ASUNEFO NORTH |
| Contact Person | Contact person name | No | John Doe |
| Contact Phone | Contact phone number | No | +233123456789 |
| Contact Email | Contact email address | No | contact@samuelotu.edu.gh |
| Is Active | Whether school is active (True/False) | No | True |

## How to Use

### Exporting Schools

1. Go to Django Admin (`/admin/`)
2. Navigate to **APPLICATIONS** → **Schools**
3. Use filters to select the schools you want to export (optional)
4. Click the **Export** button
5. Select CSV format
6. Click **Submit** to download the CSV file

### Importing Schools

1. Prepare your CSV file using the format above
2. Go to Django Admin (`/admin/`)
3. Navigate to **APPLICATIONS** → **Schools**
4. Click the **Import** button
5. Choose your CSV file
6. Review the import preview
7. Click **Submit** to import the data

### Template File

A template CSV file is available at: `media/schools_import_template.csv`

You can download this file and use it as a starting point for your import data.

## Import Rules

### School Code
- Must be unique across all schools
- Used to identify schools for updates
- If a school with the same code exists, it will be updated
- If no school with the code exists, a new one will be created

### Region Handling
- Regions are identified by name (case-insensitive)
- If a region doesn't exist, it will be created automatically
- Region code will be generated from the region name

### Data Validation
- School name, code, district, and address are required
- Contact information is optional
- Boolean fields (Is Active) accept: True, False, 1, 0, Yes, No

### Error Handling
- Invalid data will be reported during import
- You can review errors before confirming the import
- Failed rows will not be imported

## Best Practices

1. **Backup Data**: Always backup your data before bulk imports
2. **Test with Small Files**: Test imports with small CSV files first
3. **Validate Data**: Ensure your CSV data is clean and properly formatted
4. **Use Templates**: Use the provided template file as a starting point
5. **Review Results**: Always review import results and error reports

## Troubleshooting

### Common Issues

1. **Region Not Found**: Make sure region names match exactly (case-insensitive)
2. **Duplicate Codes**: Ensure school codes are unique
3. **Invalid Data**: Check that required fields are not empty
4. **File Format**: Ensure your CSV file uses UTF-8 encoding

### Getting Help

If you encounter issues:
1. Check the import error report
2. Verify your CSV format matches the template
3. Ensure all required fields are populated
4. Contact the system administrator for assistance

## Example CSV Data

```csv
ID,Name,Code,Region Name,District,Address,Contact Person,Contact Phone,Contact Email,Is Active
,SAMUEL OTU PRESBY SENIOR HIGH SCHOOL,SCH001,Ahafo Region,Asunafo North,SAMUEL OTU PRESBY SENIOR HIGH SCHOOL - ASUNEFO NORTH,John Doe,+233123456789,contact@samuelotu.edu.gh,True
,BECHEM PRESBY SENIOR HIGH SCHOOL,SCH002,Ahafo Region,Asunafo South,BECHEM PRESBY SENIOR HIGH SCHOOL - ASUNEFO SOUTH,Jane Smith,+233987654321,contact@bechempresby.edu.gh,True
```

This functionality makes it easy to manage large numbers of schools efficiently through the Django admin interface.
