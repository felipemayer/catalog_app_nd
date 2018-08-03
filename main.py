from flask import Flask, render_template
app = Flask(__name__)


@app.route("/")
def showHome():
    return render_template('home.html')


@app.route("/catalog/<int:catalogItemId>/items")
def showCatalogItems(catalogItemId):
    return render_template('items.html')


@app.route("/catalog/<int:catalogItemId>/<int:itemId>")
def showItem(catalogItemId, itemId):
    return render_template('item_detail.html')


@app.route("/catalog/<int:itemId>/edit")
def editItem(itemId):
    return render_template('item_admin.html')


@app.route("/catalog/item/new")
def newItem():
    return render_template('item_admin.html')


@app.route("/catalog/category/new")
def newCategory():
    return render_template('new_category.html')


@app.route("/catalog/<int:itemId>/delete")
def deleteItem(itemId):
    return render_template('delete.html')


@app.route("/catalog/api")
def catalogJson():
    return "Json Catalog"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
