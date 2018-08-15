import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

cat1 = Category(title="Sports", user=None)
session.add(cat1)
cat2 = Category(title="Music", user=None)
session.add(cat2)
cat3 = Category(title="Fashion", user=None)
session.add(cat3)

session.commit()
