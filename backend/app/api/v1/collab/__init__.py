"""
协作API模块
"""
from .project_routes import router as project_router
from .share_routes import router as share_router

__all__ = ["project_router", "share_router"]
