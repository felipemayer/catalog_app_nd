from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User

engine = create_engine('sqlite:///catalogapp.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def getAllCategories():
    return session.query(Category).all()


def getItemsbyQty(qty):
    return session.query(Item).order_by(
        desc(Item.updated_at)).limit(qty).all()


def getItems():
    return session.query(Item).order_by(
        desc(Item.updated_at)).all()


def getItem(itemId):
    return session.query(Item).filter_by(id=itemId).one()


def editItem(item, category, title, description):
    item.title = title
    item.description = description
    item.category = category
    session.add(item)
    session.commit()


def getItemsByCategory(categoryId):
    return session.query(Item).order_by(
        Item.created_at).filter_by(categoryId=categoryId).all()


def getItemByCategory(itemId, categoryId):
    return session.query(Item).filter_by(
        categoryId=categoryId, id=itemId).one_or_none()


def getCategoryById(categoryId):
    return session.query(Category).filter_by(id=categoryId).one()


def editCategory(category, title):
    category.title = title
    session.add(category)
    session.commit()


def getCategoryByTitle(categoryTitle):
    return session.query(Category).filter_by(
        title=categoryTitle).one()


def createItem(category, title, description, user_id):
    item = Item(title=title, description=description,
                category=category, user_id=user_id)
    session.add(item)
    session.commit()


def deleteItem(item):
    session.delete(item)
    session.commit()


def createCategory(title, userId):
    category = Category(title=title, user_id=userId)
    session.add(category)
    session.commit()


def deleteCategory(category):
    items = getItemsByCategory(category.id)
    for i in items:
        deleteItem(i)
    session.delete(category)
    session.commit()


# Crud Users
def getUserByEmail(email):
    return session.query(User).filter_by(email=email).one_or_none()


def createUser(name, email, pic):
    new_user = User(name=name, email=email, picture=pic)  # noqa
    session.add(new_user)
    session.commit()
