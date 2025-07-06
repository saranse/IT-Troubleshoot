from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class DomainBase(BaseModel):
    url: str
    group_id: Optional[int] = None
    is_active: Optional[bool] = True

class DomainCreate(DomainBase):
    pass

class DomainUpdate(DomainBase):
    url: Optional[str] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None

class DomainResponse(DomainBase):
    id: int
    last_scanned: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    name: Optional[str] = None

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Group(GroupBase):
    id: int
    created_at: datetime
    domains: List[DomainResponse] = []

    class Config:
        from_attributes = True

class KeywordBase(BaseModel):
    word: str
    is_active: Optional[bool] = True
    category: Optional[str] = None

class KeywordCreate(KeywordBase):
    pass

class KeywordUpdate(KeywordBase):
    word: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None

class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Keyword(KeywordBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class WhitelistBase(BaseModel):
    url: str
    reason: Optional[str] = None

class WhitelistCreate(WhitelistBase):
    pass

class WhitelistResponse(WhitelistBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ScanResultBase(BaseModel):
    domain_id: int
    status: str
    matches: Dict[str, Any]
    error_message: Optional[str] = None

class ScanResultCreate(ScanResultBase):
    pass

class ScanResultResponse(ScanResultBase):
    id: int
    scan_date: datetime

    class Config:
        orm_mode = True

class ConfigBase(BaseModel):
    key: str
    value: str

class ConfigCreate(ConfigBase):
    pass

class Config(ConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class ConfigurationBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class ConfigurationUpdate(ConfigurationBase):
    pass

class ConfigurationResponse(ConfigurationBase):
    id: int
    key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ScheduledScanBase(BaseModel):
    group_id: Optional[int] = None
    schedule_time: datetime
    is_recurring: bool = False
    cron_expression: Optional[str] = None
    notification_email: Optional[str] = None
    is_active: Optional[bool] = True

class ScheduledScanCreate(ScheduledScanBase):
    pass

class ScheduledScan(ScheduledScanBase):
    id: int
    created_at: datetime
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanRequest(BaseModel):
    domain: str
    keywords: Optional[List[str]] = None

class GroupScanRequest(BaseModel):
    group_id: int

class DomainMoveRequest(BaseModel):
    domain_id: int
    new_group_id: int 