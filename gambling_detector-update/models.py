from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class DomainGroup(Base):
    __tablename__ = 'domain_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    domains = relationship("Domain", back_populates="group")
    scheduled_scans = relationship("ScheduledScan", back_populates="group")

class Domain(Base):
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False, unique=True)
    group_id = Column(Integer, ForeignKey('domain_groups.id'))
    is_active = Column(Boolean, default=True)
    last_scanned = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group = relationship("DomainGroup", back_populates="domains")
    scan_results = relationship("ScanResult", back_populates="domain")

class Keyword(Base):
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    category = Column(String(50))  # e.g., 'gambling', 'adult', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Whitelist(Base):
    __tablename__ = 'whitelist'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False, unique=True)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScanResult(Base):
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey('domains.id'))
    scan_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))  # 'success', 'error', etc.
    matches = Column(JSON)  # Store keyword matches and their contexts
    error_message = Column(Text)
    
    domain = relationship("Domain", back_populates="scan_results")

class Configuration(Base):
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(JSON)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScheduledScan(Base):
    __tablename__ = "scheduled_scans"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("domain_groups.id"), nullable=True)
    schedule_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    cron_expression = Column(String, nullable=True)
    notification_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    group = relationship("DomainGroup", back_populates="scheduled_scans")