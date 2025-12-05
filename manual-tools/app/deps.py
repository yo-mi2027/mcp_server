from __future__ import annotations
from fastapi import Depends
from app.core.config import load_settings, Settings
from app.repositories.manual import ManualRepository

def get_settings() -> Settings:
    return load_settings()

def get_repo(settings: Settings = Depends(get_settings)) -> ManualRepository:
    return ManualRepository(settings)
