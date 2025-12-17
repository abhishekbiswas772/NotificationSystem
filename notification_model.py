from dataclasses import dataclass
from datetime import datetime

@dataclass
class NotificationModel:
    id : str
    idempotency_key : str 
    user_id : str 
    type : str 
    provider: str
    status : str 
    payload : dict
    atempt_count : int 
    max_retries : int 
    created_at : datetime 
    last_attempted_at : int 
    failed_at : int 
    error_message : int 
    provider_response : dict

    