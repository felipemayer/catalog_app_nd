from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, g
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalogapp.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    print(login_session['state'])
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
        response = make_response(json.dumps('Current user is already connected.'),
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

    user = session.query(User).filter_by(
        email=login_session['email']).one_or_none()
    if user == None:
        createUser()

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
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser():
    current_user = User(
        name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(current_user)
    session.commit()
    print(current_user.name + " " + str(current_user.id))


@app.before_request
def getCurrentUser():
    if 'email' in login_session:
        user = session.query(User).filter_by(
            email=login_session['email']).one_or_none()
        if user != None:
            g.user = user
            g.userId = user.id
            g.userName = user.name
            g.userPicture = user.picture
            g.userEmail = user.email
    else:
        g.user = None


@app.route("/")
def showHome():
    users = session.query(User).all()
    for u in users:
        print(str(u.id) + " " + u.name + " " + u.email)
    if 'username' in login_session:
        print(login_session['username'])
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
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            title=request.form['category']).one()
        item = Item(
            title=request.form['title'], description=request.form['description'], category=category, user_id=g.userId)
        session.add(item)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('new_item.html', categories=categories)


@app.route("/catalog/item/<int:itemId>/edit", methods=['GET', 'POST'])
def editItem(itemId):
    if 'username' not in login_session:
        return redirect('/login')
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


@app.route("/catalog/<int:catalogItemId>/<int:itemId>")
def showItem(catalogItemId, itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    return render_template('item_detail.html', item=item)


@app.route("/catalog/category/new", methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        category = Category(title=request.form['title'], user_id=g.userId)
        session.add(category)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('new_category.html')


@app.route("/catalog/category/<int:categoryId>/edit", methods=['GET', 'POST'])
def editCategory(categoryId):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=categoryId).one()
    if request.method == 'POST':
        category.title = request.form['title']
        session.add(category)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('edit_category.html', category=category)


@app.route("/catalog/item/<int:itemId>/delete", methods=['GET', 'POST'])
def deleteItem(itemId):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(id=itemId).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('delete_item.html', item=item)


@app.route("/catalog/category/<int:categoryId>/delete", methods=['GET', 'POST'])
def deleteCategory(categoryId):
    if 'username' not in login_session:
        return redirect('/login')
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


@app.route("/api/v1/catalog")
def getCatalog():
    categories = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in categories])


@app.route("/api/v1/items")
def getItems():
    items = session.query(Item).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route("/api/v1/items/<int:categoryId>")
def getItemsByCategory(categoryId):
    items = session.query(Item).filter_by(categoryId=categoryId).all()
    return jsonify(Items=[i.serialize for i in items])


if __name__ == 'main':
    app.secret_key = 'super_secret_key_xyz'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
