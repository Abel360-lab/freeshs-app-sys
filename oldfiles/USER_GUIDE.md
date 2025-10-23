# GCX Supplier Application Portal - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [For Applicants](#for-applicants)
3. [For Administrators](#for-administrators)
4. [For Approved Suppliers](#for-approved-suppliers)
5. [Multi-language Support](#multi-language-support)
6. [Theme Customization](#theme-customization)
7. [Troubleshooting](#troubleshooting)
8. [Frequently Asked Questions](#frequently-asked-questions)

## Getting Started

### Accessing the Portal

The GCX Supplier Application Portal is accessible at:
- **Application Form**: `https://your-domain.com/apply/`
- **Backoffice Portal**: `https://your-domain.com/backoffice/`
- **Supplier Portal**: `https://your-domain.com/accounts/login/`

### System Requirements

- **Web Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **JavaScript**: Must be enabled
- **Internet Connection**: Stable connection required for file uploads
- **Screen Resolution**: Minimum 1024x768 (mobile responsive)

## For Applicants

### Submitting an Application

#### Step 1: Access the Application Form

1. Navigate to `https://your-domain.com/apply/`
2. The form will load with a professional interface
3. Choose your preferred language using the language switcher
4. Optionally, customize the theme (light/dark/auto)

#### Step 2: Complete the Application Form

The application form consists of 6 steps:

**Step 1: Business Information**
- Business name (required)
- Business registration number (required)
- Email address (required)
- Phone number (required, Ghana format)
- Business address (required)
- Region selection (required)
- Business type (required)
- Years in business (required)
- Annual turnover range (required)

**Step 2: Commodities to Supply**
- Select commodities from the visual grid
- Each commodity shows an image and description
- You can select multiple commodities
- Special requirements for processed foods will be highlighted

**Step 3: Team Members**
- Add team member details
- Include their name, position, experience, and qualifications
- You can add multiple team members
- At least one team member is required

**Step 4: Next of Kin**
- Provide emergency contact information
- Include name, relationship, phone number, and address
- This is required for emergency situations

**Step 5: Bank Account Information**
- Primary bank account details
- Bank name, account number, account holder name, branch
- Secondary account (optional)
- Ensure account details are accurate for payment processing

**Step 6: Declaration and Documents**
- Upload required documents:
  - Business registration certificate
  - Tax identification number (TIN)
  - Bank account verification
  - FDA certificate (if supplying processed foods)
- Read and accept the terms and conditions
- Provide digital signature

#### Step 3: Submit Application

1. Review all information before submission
2. Click "Submit Application"
3. You'll receive a tracking code (e.g., GCX-2025-000001)
4. Save this tracking code for future reference
5. A confirmation email will be sent to your registered email

### Tracking Your Application

#### Using the Tracking Code

1. Keep your tracking code safe
2. Use it to check application status
3. Share it with GCX staff when contacting support

#### Application Statuses

- **Pending Review**: Your application has been submitted and is awaiting initial review
- **Under Review**: An administrator is currently reviewing your application
- **Approved**: Your application has been approved and a supplier account created
- **Rejected**: Your application has been rejected (you'll receive a reason)

#### Uploading Additional Documents

If requested by administrators:

1. You'll receive an email notification with upload instructions
2. Visit the document upload link provided
3. Enter your tracking code
4. Upload the requested documents
5. Documents are automatically associated with your application

### Language and Theme Options

#### Changing Language

1. Click the language switcher in the top-right corner
2. Select your preferred language from the dropdown
3. The entire form will update to your selected language
4. Your language preference is saved for the session

**Available Languages:**
- **Ghanaian Languages**: English, Akan, Twi, Ewe, Ga, Hausa
- **International Languages**: French, Spanish, German, Italian, Portuguese, Arabic, Chinese, Japanese, Korean, Russian, Hindi, Urdu

#### Customizing Theme

1. Click the theme toggle button in the header
2. Choose from three options:
   - **Auto**: Follows your system's theme preference
   - **Light**: Always use light theme
   - **Dark**: Always use dark theme
3. Theme preference is saved independently for the application form

### Mobile Usage

The application form is fully responsive and optimized for mobile devices:

- Touch-friendly interface
- Optimized form layouts for small screens
- Easy file uploads on mobile devices
- Responsive commodity selection grid

## For Administrators

### Accessing the Backoffice Portal

1. Navigate to `https://your-domain.com/backoffice/`
2. Log in with your admin credentials
3. You'll see the professional dashboard

### Dashboard Overview

The dashboard provides:

- **Live Statistics**: Total applications, pending reviews, approvals, rejections
- **Recent Applications**: Latest submissions with quick action buttons
- **Monthly Trends**: Application volume over time
- **Quick Actions**: Direct access to common tasks

### Managing Applications

#### Viewing Applications

1. Click "Applications" in the sidebar
2. Use the search bar to find specific applications
3. Filter by status, date range, or other criteria
4. Applications are displayed in a responsive table

#### Application Details

Click on any application to view detailed information:

**Application Information**
- Complete business details
- Team member information
- Next of kin details
- Bank account information
- Commodities to supply

**Document Status**
- View all uploaded documents
- Check verification status
- Download and review documents
- Add verification notes

**Timeline**
- Complete application history
- Status changes
- Document uploads
- Admin actions

#### Application Actions

**Review Process**
1. Click "Review Application" to change status to "Under Review"
2. Examine all documents and information
3. Add internal notes as needed

**Document Verification**
1. Click "View" on any document to download and review
2. Use the verification form to approve or reject documents
3. Add verification notes explaining your decision

**Request Additional Documents**
1. Click "Request Documents" if more information is needed
2. Select which documents are required
3. Add a message explaining what's needed
4. An email notification will be sent to the applicant

**Approval Process**
1. Ensure all documents are verified
2. Click "Approve Application"
3. Choose whether to create a supplier account
4. Add approval notes
5. The system will send approval notification and account details

**Rejection Process**
1. Click "Reject Application" if requirements aren't met
2. Provide a clear reason for rejection
3. Add detailed notes for the applicant
4. A rejection notification will be sent

### Document Management

#### Document Verification

1. Navigate to the Documents section
2. View all uploaded documents across applications
3. Filter by verification status
4. Bulk verify documents when appropriate

#### Document Types

- **Business Registration**: Company registration certificate
- **Tax Identification**: TIN certificate
- **Bank Verification**: Bank account verification letter
- **FDA Certificate**: Required for processed food commodities
- **Other Documents**: Additional documents as requested

### Notification Management

#### Email Templates

The system includes customizable email templates for:

- Application confirmation
- Document requests
- Approval notifications
- Rejection notifications
- General communications

#### Managing Notifications

1. Access notification templates in the admin panel
2. Customize subject lines and content
3. Use template variables for personalization
4. Test notifications before sending

### User Management

#### Creating Admin Accounts

1. Access the Django admin panel
2. Navigate to Users
3. Create new admin accounts
4. Assign appropriate permissions

#### Supplier Account Management

- Supplier accounts are automatically created upon approval
- Credentials are sent via email
- You can manually create accounts if needed
- Reset passwords when requested

### Reporting and Analytics

#### Application Reports

- Export application data to CSV/Excel
- Generate PDF reports for specific applications
- Create summary reports by date range
- Track approval rates and processing times

#### Performance Metrics

- Average processing time
- Document verification rates
- Application success rates
- User activity logs

## For Approved Suppliers

### Accessing Your Account

1. Navigate to `https://your-domain.com/accounts/login/`
2. Use the credentials sent to your email upon approval
3. You'll be prompted to change your password on first login

### Supplier Dashboard

Your dashboard shows:

- **Application Status**: Current status of your application
- **Document Status**: Verification status of uploaded documents
- **Account Information**: Your supplier account details
- **Quick Actions**: Common tasks and updates

### Managing Your Profile

#### Updating Information

1. Click "Profile" in the navigation
2. Update your business information
3. Modify contact details
4. Save changes

#### Document Management

1. View all your uploaded documents
2. Check verification status
3. Upload additional documents if requested
4. Download verified documents

#### Password Management

1. Click "Change Password" in your profile
2. Enter current password
3. Set new password
4. Confirm new password

### Application History

View all your submitted applications:

- Application tracking codes
- Submission dates
- Current status
- Document verification progress
- Admin notes and comments

## Multi-language Support

### Language Selection

Both the application form and admin portal support multiple languages:

1. **Language Switcher**: Located in the top-right corner
2. **Persistent Selection**: Your choice is remembered across sessions
3. **URL Integration**: Language is reflected in the URL (e.g., `/fr/apply/`)

### Available Languages

**Ghanaian Languages:**
- English (default)
- Akan
- Twi
- Ewe
- Ga
- Hausa

**International Languages:**
- French (Français)
- Spanish (Español)
- German (Deutsch)
- Italian (Italiano)
- Portuguese (Português)
- Arabic (العربية)
- Chinese (中文)
- Japanese (日本語)
- Korean (한국어)
- Russian (Русский)
- Hindi (हिन्दी)
- Urdu (اردو)

### Language Features

- **Complete Translation**: All interface elements are translated
- **Form Validation**: Error messages appear in selected language
- **Email Notifications**: Sent in the applicant's preferred language
- **Document Labels**: Document requirements translated appropriately

## Theme Customization

### Theme Options

The system offers three theme modes:

#### Auto Mode (Default)
- Automatically follows your operating system's theme preference
- Switches between light and dark based on system settings
- Ideal for users who prefer system-consistent appearance

#### Light Mode
- Always displays light theme
- Clean, bright interface
- Good for well-lit environments

#### Dark Mode
- Always displays dark theme
- Reduced eye strain in low-light conditions
- Modern, professional appearance

### Independent Theme Settings

- **Application Form**: Has its own theme setting
- **Admin Portal**: Has separate theme preference
- **Supplier Portal**: Independent theme selection
- **Persistent Storage**: Theme choices are saved locally

### Theme Switching

1. Click the theme toggle button
2. Button cycles through: Auto → Light → Dark → Auto
3. Changes apply immediately
4. Setting is saved for future visits

## Troubleshooting

### Common Issues

#### Application Form Issues

**Form Won't Submit**
- Check that all required fields are completed
- Ensure file uploads are within size limits (10MB max)
- Verify internet connection is stable
- Try refreshing the page and resubmitting

**File Upload Problems**
- Ensure file type is supported (PDF, DOC, DOCX, JPG, PNG)
- Check file size is under 10MB
- Try uploading one file at a time
- Clear browser cache and try again

**Language Not Changing**
- Clear browser cache and cookies
- Try refreshing the page
- Check if JavaScript is enabled
- Try a different browser

**Theme Not Applying**
- Clear browser cache
- Check if local storage is enabled
- Try refreshing the page
- Disable browser extensions temporarily

#### Login Issues

**Can't Access Admin Portal**
- Verify you're using the correct URL
- Check your username and password
- Ensure your account has admin permissions
- Contact system administrator if needed

**Supplier Account Problems**
- Check the email with your credentials
- Use the exact username and password provided
- Change password on first login
- Contact support if credentials don't work

#### Document Issues

**Can't View Documents**
- Check your internet connection
- Ensure you have permission to view the document
- Try downloading instead of viewing online
- Contact administrator if issue persists

**Document Upload Fails**
- Verify file format is supported
- Check file size is under limit
- Ensure stable internet connection
- Try uploading from different browser/device

### Getting Help

#### Contact Information

- **Technical Support**: support@gcx.com.gh
- **Application Questions**: applications@gcx.com.gh
- **Phone Support**: +233 24 123 4567
- **Office Hours**: Monday-Friday, 8:00 AM - 5:00 PM GMT

#### Before Contacting Support

1. Note your tracking code (if applicable)
2. Screenshot any error messages
3. Describe the steps you were taking when the issue occurred
4. Include your browser and operating system information

## Frequently Asked Questions

### Application Process

**Q: How long does the application process take?**
A: Initial review typically takes 3-5 business days. Complete processing depends on document verification and may take 1-2 weeks.

**Q: Can I edit my application after submission?**
A: No, applications cannot be edited after submission. Contact support if you need to make changes.

**Q: What documents are required?**
A: Required documents include business registration, TIN certificate, bank verification, and FDA certificate (for processed foods).

**Q: Can I submit multiple applications?**
A: Each business can only have one active application at a time. Complete the current process before submitting another.

### Technical Questions

**Q: What browsers are supported?**
A: The portal works with Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+. JavaScript must be enabled.

**Q: Can I use the portal on mobile devices?**
A: Yes, the portal is fully responsive and optimized for mobile devices including smartphones and tablets.

**Q: Is my data secure?**
A: Yes, all data is encrypted in transit and at rest. The system follows industry security standards.

**Q: How do I change my password?**
A: After logging in, go to your profile and click "Change Password". You'll need your current password.

### Language and Accessibility

**Q: Can I use the portal in my local language?**
A: Yes, the portal supports 16+ languages including Ghanaian languages. Use the language switcher to change.

**Q: Is the portal accessible for users with disabilities?**
A: Yes, the portal follows web accessibility guidelines and supports screen readers and keyboard navigation.

**Q: Can I switch languages during the application process?**
A: Yes, you can change languages at any time during the application process.

### Account Management

**Q: How do I get my supplier account credentials?**
A: Account credentials are automatically sent to your email when your application is approved.

**Q: What if I forget my password?**
A: Use the "Forgot Password" link on the login page. You'll receive reset instructions via email.

**Q: Can I have multiple user accounts?**
A: Each business should have one primary account. Additional users can be added by the account administrator.

### Document Management

**Q: What file formats are accepted?**
A: Accepted formats include PDF, DOC, DOCX, JPG, and PNG. Maximum file size is 10MB.

**Q: How do I know if my documents are verified?**
A: Check your application status page. Document verification status is clearly indicated.

**Q: Can I upload documents after submitting my application?**
A: Yes, if additional documents are requested by administrators, you'll receive email instructions.

### Support and Contact

**Q: How can I track my application status?**
A: Use your tracking code to check status online or contact support for updates.

**Q: Who can I contact for help?**
A: Contact our support team at support@gcx.com.gh or call +233 24 123 4567 during business hours.

**Q: What information should I include when contacting support?**
A: Include your tracking code, describe the issue clearly, and provide any relevant screenshots or error messages.

This user guide provides comprehensive information for all users of the GCX Supplier Application Portal. For additional support or questions not covered here, please contact our support team.
