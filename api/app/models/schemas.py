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
