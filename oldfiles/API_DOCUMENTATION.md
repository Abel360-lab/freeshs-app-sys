# GCX Supplier Application Portal - API Documentation

## Overview

The GCX Supplier Application Portal provides a comprehensive REST API for managing supplier applications, documents, and administrative functions. The API follows RESTful conventions and supports both public and authenticated endpoints.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Production**: `https://your-domain.com/api/`

## Authentication

### Public Endpoints
No authentication required for public endpoints.

### Admin Endpoints
Admin endpoints require authentication using Django's session authentication or token authentication.

**Session Authentication**: Login via `/accounts/admin/login/` and use session cookies.

**Token Authentication**: Include token in header:
```
Authorization: Token your-token-here
```

## Public API Endpoints

### Application Submission

#### Submit New Application
```http
POST /api/applications/submit/
```

**Request Body:**
```json
{
  "business_name": "Example Company Ltd",
  "business_registration_number": "C123456789",
  "email": "contact@example.com",
  "phone_number": "+233241234567",
  "business_address": "123 Main Street, Accra",
  "region": "greater-accra",
  "business_type": "LIMITED_LIABILITY",
  "years_in_business": 5,
  "annual_turnover": "1000000-5000000",
  "commodities_to_supply": [1, 2, 3],
  "team_members": [
    {
      "name": "John Doe",
      "position": "CEO",
      "experience_years": 10,
      "qualification": "MBA"
    }
  ],
  "next_of_kin": {
    "name": "Jane Doe",
    "relationship": "SPOUSE",
    "phone_number": "+233241234568",
    "address": "123 Main Street, Accra"
  },
  "bank_accounts": [
    {
      "bank_name": "Ghana Commercial Bank",
      "account_number": "1234567890",
      "account_name": "Example Company Ltd",
      "branch": "Accra Main Branch"
    }
  ],
  "declaration_accepted": true
}
```

**Response:**
```json
{
  "success": true,
  "tracking_code": "GCX-2025-000001",
  "message": "Application submitted successfully",
  "application_id": 123
}
```

### Application Status

#### Get Application Status
```http
GET /api/applications/{tracking_code}/status/
```

**Response:**
```json
{
  "tracking_code": "GCX-2025-000001",
  "status": "PENDING_REVIEW",
  "business_name": "Example Company Ltd",
  "submitted_date": "2025-01-10T10:30:00Z",
  "last_updated": "2025-01-10T10:30:00Z",
  "status_display": "Pending Review",
  "next_steps": "Your application is being reviewed by our team."
}
```

#### Get Outstanding Documents
```http
GET /api/applications/{tracking_code}/outstanding/
```

**Response:**
```json
{
  "tracking_code": "GCX-2025-000001",
  "outstanding_documents": [
    {
      "id": 1,
      "requirement": {
        "id": 1,
        "label": "Business Registration Certificate",
        "code": "BUSINESS_REGISTRATION",
        "description": "Official business registration certificate"
      },
      "is_required": true,
      "upload_deadline": "2025-01-20T23:59:59Z"
    }
  ]
}
```

#### Upload Document
```http
POST /api/applications/{tracking_code}/outstanding/upload/
```

**Request (multipart/form-data):**
```
document_requirement_id: 1
file: [binary file data]
```

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded successfully",
  "document_id": 456
}
```

## Admin API Endpoints

### Applications Management

#### List Applications
```http
GET /api/admin/applications/
```

**Query Parameters:**
- `status`: Filter by status (PENDING_REVIEW, UNDER_REVIEW, APPROVED, REJECTED)
- `search`: Search by business name, email, or tracking code
- `page`: Page number for pagination
- `page_size`: Number of items per page

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/admin/applications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "tracking_code": "GCX-2025-000001",
      "business_name": "Example Company Ltd",
      "email": "contact@example.com",
      "status": "PENDING_REVIEW",
      "submitted_date": "2025-01-10T10:30:00Z",
      "last_updated": "2025-01-10T10:30:00Z"
    }
  ]
}
```

#### Get Application Details
```http
GET /api/admin/applications/{id}/
```

**Response:**
```json
{
  "id": 123,
  "tracking_code": "GCX-2025-000001",
  "business_name": "Example Company Ltd",
  "email": "contact@example.com",
  "phone_number": "+233241234567",
  "business_address": "123 Main Street, Accra",
  "region": "greater-accra",
  "business_type": "LIMITED_LIABILITY",
  "years_in_business": 5,
  "annual_turnover": "1000000-5000000",
  "status": "PENDING_REVIEW",
  "submitted_date": "2025-01-10T10:30:00Z",
  "commodities": [
    {
      "id": 1,
      "name": "Maize",
      "description": "Corn grain"
    }
  ],
  "team_members": [
    {
      "id": 1,
      "name": "John Doe",
      "position": "CEO",
      "experience_years": 10,
      "qualification": "MBA"
    }
  ],
  "next_of_kin": {
    "id": 1,
    "name": "Jane Doe",
    "relationship": "SPOUSE",
    "phone_number": "+233241234568",
    "address": "123 Main Street, Accra"
  },
  "bank_accounts": [
    {
      "id": 1,
      "bank_name": "Ghana Commercial Bank",
      "account_number": "1234567890",
      "account_name": "Example Company Ltd",
      "branch": "Accra Main Branch"
    }
  ],
  "documents": [
    {
      "id": 456,
      "requirement": {
        "id": 1,
        "label": "Business Registration Certificate",
        "code": "BUSINESS_REGISTRATION"
      },
      "file": "http://localhost:8000/media/documents/business_reg_123.pdf",
      "original_filename": "business_registration.pdf",
      "uploaded_at": "2025-01-10T11:00:00Z",
      "verified": false,
      "verifier_note": null
    }
  ]
}
```

#### Request More Documents
```http
POST /api/admin/applications/{id}/request-more-docs/
```

**Request Body:**
```json
{
  "message": "Please provide your FDA certificate for processed food commodities.",
  "document_requirements": [2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Document request sent successfully",
  "outstanding_request_id": 789
}
```

#### Approve Application
```http
POST /api/admin/applications/{id}/approve/
```

**Request Body:**
```json
{
  "notes": "All requirements met. Application approved.",
  "activate_account": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Application approved successfully",
  "supplier_account_created": true,
  "email_sent": true,
  "user_id": 456
}
```

#### Reject Application
```http
POST /api/admin/applications/{id}/reject/
```

**Request Body:**
```json
{
  "reason": "Incomplete documentation provided.",
  "notes": "Please resubmit with all required documents."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Application rejected successfully",
  "email_sent": true
}
```

### Document Management

#### Verify Document
```http
POST /api/admin/documents/{id}/verify/
```

**Request Body:**
```json
{
  "action": "approve",
  "verification_notes": "Document is valid and meets requirements."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Document verified successfully",
  "verified": true
}
```

#### Get Document Details
```http
GET /api/admin/documents/{id}/
```

**Response:**
```json
{
  "id": 456,
  "application": {
    "id": 123,
    "tracking_code": "GCX-2025-000001",
    "business_name": "Example Company Ltd"
  },
  "requirement": {
    "id": 1,
    "label": "Business Registration Certificate",
    "code": "BUSINESS_REGISTRATION"
  },
  "file": "http://localhost:8000/media/documents/business_reg_123.pdf",
  "original_filename": "business_registration.pdf",
  "uploaded_at": "2025-01-10T11:00:00Z",
  "verified": true,
  "verified_at": "2025-01-10T12:00:00Z",
  "verified_by": {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator"
  },
  "verifier_note": "Document is valid and meets requirements."
}
```

### Dashboard Statistics

#### Get Dashboard Data
```http
GET /api/admin/dashboard/
```

**Response:**
```json
{
  "total_applications": 150,
  "pending_review": 45,
  "under_review": 30,
  "approved": 60,
  "rejected": 15,
  "total_suppliers": 60,
  "recent_applications": [
    {
      "id": 123,
      "tracking_code": "GCX-2025-000001",
      "business_name": "Example Company Ltd",
      "status": "PENDING_REVIEW",
      "submitted_date": "2025-01-10T10:30:00Z"
    }
  ],
  "monthly_stats": [
    {
      "month": "2025-01",
      "applications": 25,
      "approved": 12,
      "rejected": 3
    }
  ]
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes and error messages in the following format:

```json
{
  "error": "Error message description",
  "details": {
    "field_name": ["Specific field error message"]
  },
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input data
- `PERMISSION_DENIED`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `ALREADY_EXISTS`: Resource already exists
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `INVALID_FILE_TYPE`: Unsupported file type

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Public endpoints**: 100 requests per hour per IP
- **Admin endpoints**: 1000 requests per hour per user
- **File uploads**: 10 uploads per hour per IP

## WebSocket Events

### Real-time Updates

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/admin/');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'application_updated':
            // Handle application status update
            break;
        case 'new_application':
            // Handle new application notification
            break;
        case 'document_uploaded':
            // Handle document upload notification
            break;
    }
};
```

### Event Types

- `application_updated`: Application status changed
- `new_application`: New application submitted
- `document_uploaded`: Document uploaded
- `document_verified`: Document verified
- `dashboard_stats`: Dashboard statistics updated

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  timeout: 10000
});

// Submit application
async function submitApplication(applicationData) {
  try {
    const response = await api.post('/applications/submit/', applicationData);
    return response.data;
  } catch (error) {
    console.error('Error submitting application:', error.response.data);
    throw error;
  }
}

// Get application status
async function getApplicationStatus(trackingCode) {
  try {
    const response = await api.get(`/applications/${trackingCode}/status/`);
    return response.data;
  } catch (error) {
    console.error('Error getting status:', error.response.data);
    throw error;
  }
}
```

### Python

```python
import requests

class GCXAPI:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Token {token}'})
    
    def submit_application(self, application_data):
        response = self.session.post(
            f'{self.base_url}/applications/submit/',
            json=application_data
        )
        response.raise_for_status()
        return response.json()
    
    def get_application_status(self, tracking_code):
        response = self.session.get(
            f'{self.base_url}/applications/{tracking_code}/status/'
        )
        response.raise_for_status()
        return response.json()

# Usage
api = GCXAPI('http://localhost:8000/api/')
status = api.get_application_status('GCX-2025-000001')
print(status)
```

## Testing

### Postman Collection

A Postman collection is available for testing all API endpoints. Import the collection and set up environment variables for different environments.

### cURL Examples

```bash
# Submit application
curl -X POST http://localhost:8000/api/applications/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Example Company Ltd",
    "email": "contact@example.com",
    "phone_number": "+233241234567",
    "declaration_accepted": true
  }'

# Get application status
curl -X GET http://localhost:8000/api/applications/GCX-2025-000001/status/

# Approve application (admin)
curl -X POST http://localhost:8000/api/admin/applications/123/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your-token-here" \
  -d '{
    "notes": "Application approved",
    "activate_account": true
  }'
```

## Support

For API support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation for updates
