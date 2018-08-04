from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item
engine = create_engine('sqlite:///catalogapp.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route("/")
def showHome():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.updated_at)).limit(10).all()
    return render_template('home.html', categories=categories, items=items)


@app.route("/catalog/<string:categoryTitle>/<int:categoryId>/items")
def showCatalogItems(categoryTitle, categoryId):
    categories = session.query(Category).all()
    items = session.query(Item).order_by(
        Item.created_at).filter_by(categoryId=categoryId).all()
    category = session.query(Category).filter_by(id=categoryId).one()
    itemsCount = session.query(Item).filter_by(categoryId=categoryId).count()
    return render_template('items.html', categories=categories, items=items, itemsCount=itemsCount, category=category)


@app.route("/catalog/item/new", methods=['GET', 'POST'])
def newItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            title=request.form['category']).one()
        item = Item(
            title=request.form['title'], description=request.form['description'], category=category)
        session.add(item)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('new_item.html', categories=categories)


@app.route("/catalog/<int:catalogItemId>/<int:itemId>")
def showItem(catalogItemId, itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    return render_template('item_detail.html', item=item)


@app.route("/catalog/<int:itemId>/edit", methods=['GET', 'POST'])
def editItem(itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    categories = session.query(Category).all()
    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form['description']
        category = session.query(Category).filter_by(
            title=request.form['category']).one()
        item.category = category
        session.add(item)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('edit_item.html', item=item, categories=categories)


@app.route("/catalog/category/new", methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        category = Category(title=request.form['title'])
        session.add(category)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('new_category.html')


@app.route("/catalog/item/<int:itemId>/delete", methods=['GET', 'POST'])
def deleteItem(itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('delete_item.html', item=item)


@app.route("/catalog/category/<int:categoryId>/delete", methods=['GET', 'POST'])
def deleteCategory(categoryId):
    category = session.query(Category).filter_by(id=categoryId).one()
    if request.method == 'POST':
        items = session.query(Item).filter_by(categoryId=categoryId).all()
        for i in items:
            session.delete(i)
        session.delete(category)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('delete_category.html', category=category)


@app.route("/catalog/api")
def catalogJson():
    return "Json Catalog"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
