from pydantic import BaseModel


class EmailRequest(BaseModel):
    """Request model for fetching user emails."""
    user_uuid: str


class EmailResponse(BaseModel):
    """Response model for email data."""
    id: str
    thread_id: str
    from_email: str = ""
    subject: str = ""
    date: str = ""
    snippet: str = ""
    body_preview: str = ""
    invoice_indicators: list[str] = []


class EmailFetchResponse(BaseModel):
    """Response model for email fetch endpoint."""
    message: str
    user_uuid: str
    email_count: int
    search_terms: list[str]
    emails: list[EmailResponse]


class OAuthTokenRequest(BaseModel):
    """Request model for storing OAuth tokens."""
    user_id: str
    provider: str = "google"
    access_token: str
    refresh_token: str = ""
    scopes: list[str] = []
    expires_in: int = 3600  # Token expiry in seconds


class OAuthTokenResponse(BaseModel):
    """Response model for OAuth token storage."""
    message: str
    user_id: str
    provider: str
    stored: bool


class BillerProfile(BaseModel):
    """Model for a biller/company profile."""
    full_name: str  # Company name or "Full Name from Company"
    email_address: str
    domain: str = ""  # Domain name extracted from email (e.g., "netflix.com")
    profile_picture_url: str = ""
    full_address: str = ""
    payment_method: str = ""  # e.g., "Credit Card", "Bank Transfer", etc.
    billing_info: str = ""  # Bank details, account numbers, etc.
    frequency: str = ""  # Detected billing frequency (e.g., "Monthly", "Weekly", "One-time")
    source_emails: list[str] = []  # Email IDs where this biller was found (unique invoices only)
    total_invoices: int = 0  # Count of unique invoices (excludes drafts/adjustments)


class BillerProfilesResponse(BaseModel):
    """Response model for biller profiles extraction."""
    message: str
    user_uuid: str
    total_billers: int
    profiles: list[BillerProfile]
