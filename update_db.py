import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

cats = session.query(Category).delete()
items = session.query(Item).delete()
user = session.query(User).delete()

user1 = User(name="Felipe", email="fesssss@mayaaer.com")
session.add(user1)

user2 = User(name="Paula", email="paula@bergaaamaschi.aaaacom")
session.add(user2)

cat1 = Category(title="Categoria 1", user=user1)
session.add(cat1)
cat2 = Category(title="Categoria 2", user=user2)
session.add(cat2)

item1 = Item(title="Item 1 - cat1",
             description="bla bla bla item1", categoryId=1, user=user1)
session.add(item1)
item2 = Item(title="Item 1 - cat1",
             description="bla bla bla item1", categoryId=1, user=user2)
session.add(item2)
item3 = Item(title="Item 1 - cat2",
             description="bla bla bla item1", categoryId=2, user=user1)
session.add(item3)
item4 = Item(title="Item 1 - cat2",
             description="bla bla bla item1", categoryId=2, user=user1)
session.add(item4)
item5 = Item(title="Item 1 - cat2",
             description="bla bla bla item1", categoryId=2, user=user1)
session.add(item5)
item6 = Item(title="Item 1 - cat2",
             description="bla bla bla item1", categoryId=2, user=user1)
session.add(item6)

session.commit()
