"""
Test factories for creating test data
"""
import factory
from factory import Factory, Faker, SubFactory, LazyAttribute, Sequence
from faker import Faker as FakerInstance
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.models.user import User
from app.models.item import Item
from app.core.security import get_password_hash

# Create a Faker instance for more advanced fake data
fake = FakerInstance()


class BaseFactory(Factory):
    """Base factory class"""
    
    class Meta:
        abstract = True


class UserFactory(BaseFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
    
    email = Sequence(lambda n: f'user{n}@example.com')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    hashed_password = LazyAttribute(lambda obj: get_password_hash('TestPassword123'))
    is_active = True
    is_superuser = False
    created_at = LazyAttribute(lambda obj: fake.date_time_between(start_date='-30d', end_date='now'))
    updated_at = LazyAttribute(lambda obj: obj.created_at)


class SuperUserFactory(UserFactory):
    """Factory for creating test superusers"""
    
    email = Sequence(lambda n: f'admin{n}@example.com')
    first_name = 'Admin'
    last_name = 'User'
    is_superuser = True


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive test users"""
    
    email = Sequence(lambda n: f'inactive{n}@example.com')
    is_active = False


class ItemFactory(BaseFactory):
    """Factory for creating test items"""
    
    class Meta:
        model = Item
    
    title = Faker('sentence', nb_words=3)
    description = Faker('text', max_nb_chars=200)
    created_at = LazyAttribute(lambda obj: fake.date_time_between(start_date='-30d', end_date='now'))
    updated_at = LazyAttribute(lambda obj: obj.created_at)
    # owner_id should be set when creating the item


class PublicItemFactory(ItemFactory):
    """Factory for creating public test items"""
    
    title = LazyAttribute(lambda obj: f'Public {fake.word().capitalize()} Item')
    description = LazyAttribute(lambda obj: f'This is a public item about {fake.word()}')


class PrivateItemFactory(ItemFactory):
    """Factory for creating private test items"""
    
    title = LazyAttribute(lambda obj: f'Private {fake.word().capitalize()} Item')
    description = LazyAttribute(lambda obj: f'This is a private item about {fake.word()}')


def create_user(db: Session, **kwargs) -> User:
    """Create a user in the database"""
    # Handle custom password
    password = kwargs.pop('password', None)
    
    user_data = UserFactory.build(**kwargs)
    
    # If a custom password was provided, hash it
    if password:
        user_data.hashed_password = get_password_hash(password)
    
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=user_data.hashed_password,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_superuser(db: Session, **kwargs) -> User:
    """Create a superuser in the database"""
    # Handle custom password
    password = kwargs.pop('password', None)
    
    user_data = SuperUserFactory.build(**kwargs)
    
    # If a custom password was provided, hash it
    if password:
        user_data.hashed_password = get_password_hash(password)
    
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=user_data.hashed_password,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_item(db: Session, owner_id: int, **kwargs) -> Item:
    """Create an item in the database"""
    item_data = ItemFactory.build(**kwargs)
    item = Item(
        title=item_data.title,
        description=item_data.description,
        owner_id=owner_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_user_token_headers(client, email: str = "test@example.com", password: str = "TestPassword123") -> dict:
    """Get authentication headers for a user"""
    login_data = {
        "username": email,
        "password": password
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}, {response.text}")
        raise ValueError(f"Failed to login: {response.status_code}")
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def get_superuser_token_headers(client, email: str = "admin@example.com", password: str = "TestPassword123") -> dict:
    """Get authentication headers for a superuser"""
    return get_user_token_headers(client, email, password)


# Batch creation helpers
def create_multiple_users(db: Session, count: int = 5, **kwargs) -> list[User]:
    """Create multiple users at once"""
    users = []
    for i in range(count):
        user_kwargs = {**kwargs, 'email': f'user{i}@example.com'}
        # Remove password if present since User model doesn't have password field
        user_kwargs.pop('password', None)
        user = create_user(db, **user_kwargs)
        users.append(user)
    return users


def create_multiple_items(db: Session, owner_id: int, count: int = 5, **kwargs) -> list[Item]:
    """Create multiple items for a user"""
    items = []
    for i in range(count):
        item_kwargs = {**kwargs}
        if 'title' not in item_kwargs:
            item_kwargs['title'] = f'Test Item {i+1}'
        item = create_item(db, owner_id, **item_kwargs)
        items.append(item)
    return items


def create_user_with_items(db: Session, item_count: int = 3, **user_kwargs) -> tuple[User, list[Item]]:
    """Create a user with associated items"""
    user = create_user(db, **user_kwargs)
    items = create_multiple_items(db, user.id, item_count)
    return user, items


def create_complete_test_data(db: Session) -> dict:
    """Create a complete set of test data"""
    # Create superuser
    superuser = create_superuser(db, email='admin@example.com')
    
    # Create regular users
    users = create_multiple_users(db, count=5)
    
    # Create inactive user
    inactive_user = create_user(db, email='inactive@example.com', is_active=False)
    
    # Create items for each user
    all_items = []
    for user in users:
        items = create_multiple_items(db, user.id, count=3)
        all_items.extend(items)
    
    return {
        'superuser': superuser,
        'users': users,
        'inactive_user': inactive_user,
        'items': all_items
    }


# Test data generators
class TestDataGenerator:
    """Class for generating various test data scenarios"""
    
    @staticmethod
    def generate_user_data(user_type: str = 'regular') -> dict:
        """Generate user data for different scenarios"""
        base_data = {
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'password': 'TestPassword123'
        }
        
        if user_type == 'superuser':
            base_data.update({
                'is_superuser': True,
                'email': f'admin_{fake.word()}@example.com'
            })
        elif user_type == 'inactive':
            base_data.update({
                'is_active': False,
                'email': f'inactive_{fake.word()}@example.com'
            })
        
        return base_data
    
    @staticmethod
    def generate_item_data(item_type: str = 'regular') -> dict:
        """Generate item data for different scenarios"""
        base_data = {
            'title': fake.sentence(nb_words=3),
            'description': fake.text(max_nb_chars=200)
        }
        
        if item_type == 'long_title':
            base_data['title'] = fake.text(max_nb_chars=100)
        elif item_type == 'long_description':
            base_data['description'] = fake.text(max_nb_chars=1000)
        elif item_type == 'minimal':
            base_data.update({
                'title': fake.word(),
                'description': fake.sentence()
            })
        
        return base_data
    
    @staticmethod
    def generate_auth_data(scenario: str = 'valid') -> dict:
        """Generate authentication data for different test scenarios"""
        if scenario == 'valid':
            return {
                'username': 'test@example.com',
                'password': 'TestPassword123'
            }
        elif scenario == 'invalid_email':
            return {
                'username': 'nonexistent@example.com',
                'password': 'TestPassword123'
            }
        elif scenario == 'invalid_password':
            return {
                'username': 'test@example.com',
                'password': 'wrongpassword'
            }
        elif scenario == 'malformed':
            return {
                'username': 'not-an-email',
                'password': '123'
            }
        
        return {}