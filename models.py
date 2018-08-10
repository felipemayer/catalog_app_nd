from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    picture = Column(String(250))
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(String(400), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    categoryId = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.categoryId,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.create_all(engine)
