# database/__init__.py
from .models import Base
from .crud import db_manager

__all__ = ['Base', 'db_manager']