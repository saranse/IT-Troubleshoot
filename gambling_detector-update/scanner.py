from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class DomainBase(BaseModel):
    name: str

class DomainCreate(DomainBase):
    pass

class Domain(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_at: datetime
    domains: List[Domain] = []

    class Config:
        from_attributes = True

class KeywordBase(BaseModel):
    word: str

class KeywordCreate(KeywordBase):
    pass

class Keyword(KeywordBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class WhitelistBase(BaseModel):
    url: HttpUrl
    note: Optional[str] = None

class WhitelistCreate(WhitelistBase):
    pass

class Whitelist(WhitelistBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ScanResultBase(BaseModel):
    domain_id: int
    keyword: str
    url: str
    title: str
    matches: str

class ScanResult(ScanResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

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

class ScheduledScanBase(BaseModel):
    group_id: Optional[int] = None
    schedule_time: datetime
    is_recurring: bool = False
    cron_expression: Optional[str] = None
    notification_email: Optional[str] = None

class ScheduledScanCreate(ScheduledScanBase):
    pass

class ScheduledScan(ScheduledScanBase):
    id: int
    created_at: datetime
    last_run: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True

class ScanRequest(BaseModel):
    domain: str
    keywords: List[str]

class GroupScanRequest(BaseModel):
    group_id: int

class DomainMoveRequest(BaseModel):
    domain_id: int
    new_group_id: int 