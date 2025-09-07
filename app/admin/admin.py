"""
SQLAdmin configuration for admin interface
"""
from sqladmin import Admin, ModelView
from sqlalchemy import create_engine

from app.core.config import settings
from app.models.user import User
from app.models.item import Item
from app.admin.auth import AdminAuthBackend


def create_sync_engine():
    """Create synchronous engine for admin interface"""
    # Convert async URL to sync URL for SQLAdmin
    if settings.ENVIRONMENT == "testing" or "sqlite" in settings.DATABASE_URL:
        # Use SQLite for testing
        sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")
    else:
        # Use PostgreSQL for production
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(sync_url)


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""
    name = "User"
    identity = "user"
    
    column_list = [User.id, User.email, User.first_name, User.last_name, User.is_active, User.is_superuser, User.created_at]
    column_details_exclude_list = [User.hashed_password]
    column_searchable_list = [User.email, User.first_name, User.last_name]
    column_sortable_list = [User.id, User.email, User.created_at, User.is_active]
    column_default_sort = [(User.created_at, True)]
    
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    # Column labels
    column_labels = {
        User.id: "ID",
        User.email: "Email",
        User.first_name: "First Name", 
        User.last_name: "Last Name",
        User.is_active: "Active",
        User.is_superuser: "Superuser",
        User.created_at: "Created At",
        User.updated_at: "Updated At"
    }
    
    # Display options
    page_size = 20
    page_size_options = [10, 20, 50, 100]


class ItemAdmin(ModelView, model=Item):
    """Admin view for Item model"""
    name = "Item"
    identity = "item"
    
    column_list = [Item.id, Item.title, Item.owner_id, Item.is_active, Item.created_at]
    column_searchable_list = [Item.title, Item.description]
    column_sortable_list = [Item.id, Item.title, Item.created_at, Item.is_active]
    column_default_sort = [(Item.created_at, True)]
    
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    # Column labels
    column_labels = {
        Item.id: "ID",
        Item.title: "Title",
        Item.description: "Description",
        Item.owner_id: "Owner ID",
        Item.is_active: "Active",
        Item.created_at: "Created At",
        Item.updated_at: "Updated At"
    }
    
    # Display options
    page_size = 20
    page_size_options = [10, 20, 50, 100]


def setup_admin(app):
    """Setup SQLAdmin with the FastAPI app"""
    engine = create_sync_engine()
    authentication_backend = AdminAuthBackend()
    
    admin = Admin(
        app=app,
        engine=engine,
        title=settings.ADMIN_TITLE,
        logo_url=settings.ADMIN_LOGO_URL,
        base_url="/admin",
        authentication_backend=authentication_backend,
        debug=True,  # Enable debug mode for troubleshooting
    )
    
    # Add model views
    admin.add_view(UserAdmin)
    admin.add_view(ItemAdmin)
    
    print(f"SQLAdmin setup complete with {len(admin._views)} views:")
    for view in admin._views:
        print(f"  - {view.__class__.__name__}: {view.identity}")
    
    return admin