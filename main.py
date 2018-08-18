from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, g, abort, make_response  # noqa
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import crud
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    print(login_session['state'])
    return render_template('login.html', STATE=state)


@app.route('/logout')
def logout():
    return render_template('logout.html')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps(
            'Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),  # noqa
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user = crud.getUserByEmail(login_session['email'])
    if user is None:
        crud.createUser(
            login_session['username'], login_session['email'], login_session['picture'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showHome'))
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    #  success on logout
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showHome'))
    #  fail on logout
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showHome'))


#  before request check if user is logged


@app.before_request
def getCurrentUser():
    if 'email' in login_session:
        user = crud.getUserByEmail(login_session['email'])
        #  if user is logged update global data g
        if user is not None:
            g.user = user
            g.userId = user.id
            g.userName = user.name
            g.userPicture = user.picture
            g.userEmail = user.email
    else:
        g.user = None


def userIsLogged():
    return False if 'username' not in login_session else True


def userIsOwner(item_or_category):
    return True if item_or_category.user_id == g.userId else False

#  routes from ui


@app.route("/")
def showHome():
    categories = crud.getAllCategories()
    items = crud.getItemsbyQty(10)
    return render_template('home.html', categories=categories, items=items)


@app.route("/catalog/<int:categoryId>/items")
def showCatalogItems(categoryId):
    categories = crud.getAllCategories()
    items = crud.getItemsByCategory(categoryId)
    category = crud.getCategoryById(categoryId)
    logged = userIsLogged()
    owner = userIsOwner(category) if logged else False
    return render_template('items.html', categories=categories, items=items, itemsCount=len(items), category=category, logged=logged, owner=owner)  # noqa


@app.route("/catalog/item/new", methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    categories = crud.getAllCategories()
    if request.method == 'POST':
        category = crud.getCategoryByTitle(request.form['category'])
        crud.createItem(
            category, request.form['title'], request.form['description'], g.userId)
        return redirect(url_for('showHome'))
    else:
        return render_template('new_item.html', categories=categories)


@app.route("/catalog/item/<int:itemId>/edit", methods=['GET', 'POST'])
def editItem(itemId):
    if 'username' not in login_session:
        return redirect('/login')
    item = crud.getItem(itemId)
    categories = crud.getAllCategories()
    if request.method == 'POST':
        category = crud.getCategoryByTitle(request.form['category'])
        crud.editItem(item, category,
                      request.form['title'], request.form['description'])
        return redirect(url_for('showHome'))
    else:
        return render_template('edit_item.html', item=item, categories=categories)  # noqa


@app.route("/catalog/<int:catalogItemId>/<int:itemId>")
def showItem(catalogItemId, itemId):
    item = crud.getItem(itemId)
    logged = userIsLogged()
    owner = userIsOwner(item) if logged else False
    return render_template('item_detail.html', item=item, logged=logged, owner=owner)


@app.route("/catalog/category/new", methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        crud.createCategory(request.form['title'], g.userId)
        return redirect(url_for('showHome'))
    else:
        return render_template('new_category.html')


@app.route("/catalog/category/<int:categoryId>/edit", methods=['GET', 'POST'])
def editCategory(categoryId):
    if 'username' not in login_session:
        return redirect('/login')
    category = crud.getCategoryById(categoryId)
    if request.method == 'POST':
        crud.editCategory(category, request.form['title'])
        return redirect(url_for('showHome'))
    else:
        return render_template('edit_category.html', category=category)


@app.route("/catalog/item/<int:itemId>/delete", methods=['GET', 'POST'])
def deleteItem(itemId):
    if 'username' not in login_session:
        return redirect('/login')
    item = crud.getItem(itemId)
    if request.method == 'POST':
        crud.deleteItem(item)
        return redirect(url_for('showHome'))
    else:
        return render_template('delete_item.html', item=item)


@app.route("/catalog/category/<int:categoryId>/delete", methods=['GET', 'POST'])  # noqa
def deleteCategory(categoryId):
    if 'username' not in login_session:
        return redirect('/login')
    category = crud.getCategoryById(categoryId)
    if request.method == 'POST':
        crud.deleteCategory(category)
        return redirect(url_for('showHome'))
    else:
        return render_template('delete_category.html', category=category)

#  /api/ responses

#  get all categories


@app.route("/api/v1/catalog")
def getCategories():
    categories = crud.getAllCategories()
    return jsonify(Category=[c.serialize for c in categories])

#  get all items


@app.route("/api/v1/items")
def getItems():
    items = crud.getItems()
    return jsonify(Items=[i.serialize for i in items])


#  get all itens from category

@app.route("/api/v1/items/<int:categoryId>")
def getItemsByCategory(categoryId):
    items = crud.getItemsByCategory(categoryId)
    return jsonify(Items=[i.serialize for i in items])


#  get especific item

@app.route("/api/v1/<int:categoryId>/<int:itemId>")
def getItem(categoryId, itemId):
    item = crud.getItemByCategory(itemId, categoryId)
    return jsonify(item.serialize) if item is not None else abort(404)


if __name__ == 'main':
    app.secret_key = 'super_secret_key_xyz'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
