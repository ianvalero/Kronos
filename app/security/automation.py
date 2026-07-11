import hmac
from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config.settings import settings
from app.exceptions import InvalidAutomationTokenError

automation_token_header = APIKeyHeader(name="X-Automation-Token", scheme_name="AutomationTokenAuth", auto_error=False)

def require_automation(token: str = Security(automation_token_header)) -> None:
    if not token or not hmac.compare_digest(token, settings.automation_api_token):
        raise InvalidAutomationTokenError("Invalid automation token")