"""
Authentication backend for SQLAdmin
"""
from typing import Optional
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User


class AdminAuthBackend(AuthenticationBackend):
    """Custom authentication backend for admin interface"""
    
    def __init__(self):
        super().__init__(secret_key=settings.ADMIN_SECRET_KEY)
        # Create sync engine for authentication
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        self.engine = create_engine(sync_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    async def login(self, request: Request) -> bool:
        """Handle login form submission"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        print(f"Login attempt: {username}")
        
        if not username or not password:
            print("Missing credentials")
            return False
        
        # Authenticate user
        with self.SessionLocal() as db:
            try:
                user = db.execute(select(User).filter(User.email == username)).scalar_one_or_none()
                
                if user and user.is_active and user.is_superuser:
                    if verify_password(password, user.hashed_password):
                        # Store user info in session
                        request.session.update({
                            "token": "authenticated",
                            "user_id": user.id,
                            "user_email": user.email
                        })
                        print(f"Login successful for {user.email}")
                        return True
                    else:
                        print("Password verification failed")
                else:
                    print(f"User validation failed: user={bool(user)}, active={user.is_active if user else False}, superuser={user.is_superuser if user else False}")
                        
            except Exception as e:
                print(f"Authentication error: {e}")
                return False
                
        print("Login failed")
        return False
    
    async def logout(self, request: Request) -> bool:
        """Handle logout"""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Check if user is authenticated for protected routes"""
        # Skip authentication for login page and static assets
        if request.url.path.endswith("/login") or "/static/" in request.url.path:
            return None
            
        token = request.session.get("token")
        print(f"Authenticate check: path={request.url.path}, token={token}, session_keys={list(request.session.keys())}")
        
        if not token:
            print(f"No token, redirecting to login")
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        
        # Verify user still exists and is active superuser
        user_id = request.session.get("user_id")
        if user_id:
            with self.SessionLocal() as db:
                try:
                    user = db.execute(select(User).filter(User.id == user_id)).scalar_one_or_none()
                    if not user or not user.is_active or not user.is_superuser:
                        print(f"User validation failed during auth check, clearing session")
                        request.session.clear()
                        return RedirectResponse(request.url_for("admin:login"), status_code=302)
                    else:
                        print(f"User validation successful: {user.email}")
                except Exception as e:
                    print(f"Error during auth check: {e}")
                    request.session.clear()
                    return RedirectResponse(request.url_for("admin:login"), status_code=302)
        
        print(f"Authentication successful for path: {request.url.path}")
        return None