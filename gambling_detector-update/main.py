from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime, timedelta
import asyncio

from .database import get_db, get_redis, engine
from . import models, schemas
from .worker import scan_domain_task
from rq import Queue
from rq.job import Job

app = FastAPI(
    title="Gambling Domain Detector",
    description="API for detecting gambling-related content on domains",
    version="2.0.0"
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis queue
redis_conn = get_redis()
scan_queue = Queue(connection=redis_conn)

# Domain endpoints
@app.post("/domains/", response_model=schemas.DomainResponse)
def create_domain(domain: schemas.DomainCreate, db: Session = Depends(get_db)):
    db_domain = models.Domain(url=domain.url, group_id=domain.group_id)
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    return db_domain

@app.get("/domains/", response_model=List[schemas.DomainResponse])
def list_domains(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    domains = db.query(models.Domain).offset(skip).limit(limit).all()
    return domains

@app.delete("/domains/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(domain)
    db.commit()
    return {"message": "Domain deleted"}

# Group endpoints
@app.post("/groups/", response_model=schemas.GroupResponse)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = models.DomainGroup(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/groups/", response_model=List[schemas.GroupResponse])
def list_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = db.query(models.DomainGroup).offset(skip).limit(limit).all()
    return groups

@app.post("/groups/move-domain")
def move_domain(move_request: schemas.DomainMoveRequest, db: Session = Depends(get_db)):
    domain = db.query(models.Domain).filter(models.Domain.id == move_request.domain_id).first()
    new_group = db.query(models.DomainGroup).filter(models.DomainGroup.id == move_request.new_group_id).first()
    
    if not domain or not new_group:
        raise HTTPException(status_code=404, detail="Domain or group not found")
        
    domain.group_id = new_group.id
    db.commit()
    return {"message": "Domain moved successfully"}

# Keyword endpoints
@app.post("/keywords/", response_model=schemas.KeywordResponse)
def create_keyword(keyword: schemas.KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = models.Keyword(**keyword.dict())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@app.get("/keywords/", response_model=List[schemas.KeywordResponse])
def list_keywords(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    keywords = db.query(models.Keyword).offset(skip).limit(limit).all()
    return keywords

# Whitelist endpoints
@app.post("/whitelist/", response_model=schemas.WhitelistResponse)
def create_whitelist(whitelist: schemas.WhitelistCreate, db: Session = Depends(get_db)):
    db_whitelist = models.Whitelist(**whitelist.dict())
    db.add(db_whitelist)
    db.commit()
    db.refresh(db_whitelist)
    return db_whitelist

@app.get("/whitelist/", response_model=List[schemas.WhitelistResponse])
def list_whitelist(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    whitelist = db.query(models.Whitelist).offset(skip).limit(limit).all()
    return whitelist

# Scan endpoints
@app.post("/scan/test")
async def test_scan(scan_request: schemas.ScanRequest):
    results = scan_domain_task(scan_request.domain, scan_request.keywords)
    return results

@app.post("/scan/group/{group_id}")
def scan_group(group_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    group = db.query(models.DomainGroup).filter(models.DomainGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Enqueue scan job for each domain in the group
    jobs = []
    for domain in group.domains:
        job = scan_queue.enqueue(scan_domain_task, domain.url)
        jobs.append(job.id)
    
    return {"message": "Scan started", "job_ids": jobs}

# Schedule endpoints
@app.post("/schedule/", response_model=schemas.ScheduledScan)
def create_schedule(schedule: schemas.ScheduledScanCreate, db: Session = Depends(get_db)):
    db_schedule = models.ScheduledScan(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@app.get("/schedule/", response_model=List[schemas.ScheduledScan])
def list_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = db.query(models.ScheduledScan).offset(skip).limit(limit).all()
    return schedules

# Results endpoints
@app.get("/results/", response_model=List[schemas.ScanResultResponse])
def list_results(
    skip: int = 0,
    limit: int = 100,
    days: int = 7,
    db: Session = Depends(get_db)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    results = db.query(models.ScanResult)\
        .filter(models.ScanResult.scan_date >= cutoff_date)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return results

# Config endpoints
@app.post("/config/", response_model=schemas.Configuration)
def update_config(config: schemas.ConfigurationUpdate, db: Session = Depends(get_db)):
    db_config = db.query(models.Configuration).filter(models.Configuration.key == config.key).first()
    if db_config:
        for key, value in config.dict(exclude_unset=True).items():
            setattr(db_config, key, value)
    else:
        db_config = models.Configuration(**config.dict())
        db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@app.get("/config/{key}", response_model=schemas.Configuration)
def get_config(key: str, db: Session = Depends(get_db)):
    config = db.query(models.Configuration).filter(models.Configuration.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config