# Python script using Flask.
# Control the functionality of the Website.

from flask import Flask, render_template, request, redirect, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


'''
Website
'''

# Login Page
# Get the login credentials from the user and validates it.
@app.route('/login', methods=['POST'])
def do_admin_login():

    # Get the username and password from the login form
    un = request.form['get_un']
    pswd = request.form['get_pswd']

    # Check if the login credential is valid
    query = "Select * from Users WHERE username = '%s' AND password = '%s';"
    rslt = getQueryResult(query % (un, pswd))

    if len(rslt) == 0:
        return render_template('login.html', msg='Wrong username/password')

    for r in rslt:
        # Set the username and get the teamname of the user
        session['username'] = un
    return index()

# Logout Page
# Logs out the current user and redirects to login page.
@app.route("/logout")
def logout():
    session.pop('username', None)
    return index()

# Homepage
# This page shows the menu page.
@app.route('/')
def index():

    # Check if logged_in
    if 'username' in session:
        # logged_in. Redirect to menu page.
        return render_template("index.html", user=session['username'])

    # Not logged_in. Redirect to login page.
    return render_template('login.html' , msg='')

# Search page
# Shows the current Stock and ItemsUsed table and allows the user
# to search based on ID or Tag name or Tech name.
@app.route('/search', methods = ['GET', 'POST'])
def search():

    if 'username' not in session:
        # Not logged_in. Redirect to login page.
        return render_template('login.html')

    if request.method == 'GET':
        return render_template("search.html", user=session['username'], search='',
                               stockRslt=getStock(), useRslt=getInUse())
    else:
        # Get the query string to search from the user
        search = (request.form['searchString']).strip()
        if (search == ''):
            # Empty string displays everything
            stockRslt = getStock()
            useRslt = getInUse()
            return render_template("search.html", user=session['username'], search='',
                                   stockRslt=stockRslt, useRslt = useRslt)

        query = "Select * from Stock WHERE TechName = '%s' OR \
                ID = '%s' OR \
                ID IN (Select ID from Tags WHERE TAG = '%s');"
        # Insert the search query and
        # get the result of executing it in the Stock Table.
        stockRslt = getQueryResult(query % (search, search, search))

        query = "Select i.ID, s.TechName, i.UnitsUsed, i.UsedIn, i.UsedBy \
                from ItemsUsed i, Stock s WHERE \
                s.ID = i.ID AND \
                (i.ID IN (Select a.ID from Stock a WHERE a.TechName = '%s') OR \
                i.ID = '%s' OR \
                i.ID IN (Select t.ID from Tags t WHERE t.TAG = '%s'));"
        # Insert the search query and
        # get the result of executing it in the ItemsUsed Table.
        useRslt = getQueryResult(query % (search, search, search))

        # Display the result on the same page.
        return render_template("search.html", user=session['username'], search=search,
                               stockRslt=stockRslt, useRslt=useRslt)

# Add item page
# There are 2 ways of adding items into the Inventory.
# -> Add a new item
# -> Add an existing item
@app.route('/add/<int:task>', methods = ['GET', 'POST'])
def add(task):

    if 'username' not in session:
        # Not logged_in. Redirect to login page.
        return render_template('login.html')

    # Display options for how to add item
    if(task == 0 or request.method == 'GET'):
        return render_template("add.html", user=session['username'], task=task,
                               result=0, display='', stockRslt=getStock())

    # Add a new item
    elif (task == 1):
        # Get the name, no of units being added, description and tags
        # for the new item from the user via the input form.
        get_name = request.form['get_name']
        get_units = request.form['get_units']
        get_descp = request.form['get_descp']
        get_tags = request.form['get_tags']

        # Verify that none of the inputs is empty.
        if (get_name == '' or get_units == '' or get_descp == '' or get_tags == ''):
            display="Empty field detected"
            return render_template("add.html", user=session['username'], task=task,
                                   result=-1, display=display, stockRslt=getStock())

        # Verify that the no of units being added is not negative.
        if (get_units < 0):
            display=("Invalid input for items to add: '%s'" % (get_units))
            return render_template("add.html", user=session['username'], task=task,
                                   result=-1, display=display, stockRslt=getStock())

        # Ready to add the new item to the table.

        # Generate an ID for the item
        get_id = getNewID()

        # Add the item to the Stock table
        # Also register the name of the user doing the change.
        # Commit the changes to the table.
        exec_commit("Insert into Stock VALUES (%s, '%s', 0, %s, '%s', '%s');"
                        % (get_id, get_name, get_units, get_descp, session['username']))

        # Get each tag for the item
        tags = get_tags.split(",")

        # Add each tag for the item in the Tags table
        for tag in tags:
            newTag = tag.strip()
            if (newTag != ''):
                exec_commit("Insert into Tags VALUES (%s, '%s');" % (get_id, newTag))

        # Success. Stays on the same page and resets the form.
        return render_template("add.html", user=session['username'], task=task,
                               result=1, display="Success!", stockRslt=getStock())

    # Add an existing item
    else:
        # Get the ID of the already existing item and the number of units of
        # the item to be added from the user via the input form.
        get_id = int(request.form['get_id'])
        get_units = int(request.form['get_units'])

        # Verify that none of the inputs is empty.
        if (get_id == '' or get_units == ''):
            display="Empty field detected"
            return render_template("add.html", user=session['username'], task=task,
                                   result=-1, display=display, stockRslt=getStock())

        # Verify that the no of units being added is not negative.
        if (get_units <= 0):
            display=("Invalid input for items to add: '%s'" % (get_units))
            return render_template("add.html", user=session['username'], task=task,
                                   result=-1, display=display, stockRslt=getStock())

        # Verify that an item with the ID exists int the table.
        query = "SELECT ID, UnitsAvail from Stock WHERE ID = %s;"
        qrslt = getQueryResult(query % get_id)

        if (len(qrslt) == 0):
            # No item with the ID found.
            display=("No item with ID: '%s' found." % (get_id))
            return render_template("add.html", user=session['username'], task=task,
                                   result=-1, display=display, stockRslt=getStock())

        # Add the units for the item.
        # Also register the name of the user doing the change.
        # Commit the changes to the table.
        exec_commit("UPDATE Stock " +
                    "SET UnitsAvail = UnitsAvail + %d WHERE ID = %d;"
                    % (get_units, get_id))
        exec_commit("UPDATE Stock " +
                    "SET LastUpdated = '%s' WHERE ID = %d;"
                    % (session['username'], get_id))

        # Success. Stays on the same page and resets the form.
        return render_template("add.html", user=session['username'], task=task,
                               result=1, display="Success!", stockRslt=getStock())

# Remove item page
@app.route('/remove', methods = ['GET', 'POST'])
def remove():

    if 'username' not in session:
        # Not logged_in. Redirect to login page.
        return render_template('login.html')

    if request.method == 'GET':
        return render_template("remove.html", user=session['username'],
                               result=0, display='', stockRslt=getStock())
    else:
        # Get the ID of the item, the number of units of to be removed
        # and the description for the use of the item from the user via the input form.
        get_id = request.form['get_id']
        get_units = request.form['get_units']
        get_descp = request.form['get_descp']

        # Verify that none of the inputs is empty.
        if (get_id == '' or get_units == '' or get_descp == ''):
            display="Empty field detected"
            return render_template("remove.html", user=session['username'],
                                   result=-1, display=display, stockRslt=getStock())

        query = "SELECT ID, UnitsAvail from Stock WHERE ID = %s;"
        unitsAvail = getUnitsAvail(query % (get_id))

        # Check if an item with the given ID exists.
        if (unitsAvail == -1):
            display=("No item with ID: '%s' found." % (get_id))
            return render_template("remove.html", user=session['username'],
                                   result=-1, display=display, stockRslt=getStock())

        # Verify that the items to be removed is positive.
        if (get_units <= 0):
            display=("Invalid input for item to use: '%s'" % (get_units))
            return render_template("remove.html", user=session['username'],
                                   result=-1, display=display, stockRslt=getStock())

        # Check if there are enough units of the item available.
        if (int(get_units) > int(unitsAvail)):
            display=("Available units: '%s'. Units demanded: '%s'" % (unitsAvail, get_units))
            return render_template("remove.html", user=session['username'],
                                   result=-1, display=display, stockRslt=getStock())

        # Remove the units for the item.
        # Also register the name of the user doing the change.
        # Commit the changes to the tables.
        exec_commit("UPDATE Stock " +
                    "SET UnitsAvail = UnitsAvail - %s WHERE ID = %s;"
                    % (get_units, get_id))
        exec_commit("UPDATE Stock " +
                    "SET UnitsUsed = UnitsUsed + %s WHERE ID = %s;"
                    % (get_units, get_id))
        exec_commit("UPDATE Stock " +
                    "SET LastUpdated = '%s' WHERE ID = %s;"
                    % (session['username'], get_id))
        exec_commit("Insert into ItemsUsed VALUES (%s, %s, '%s', '%s');"
                    % (get_id, get_units, get_descp, session['username']))

        # Success. Stays on the same page and resets the form.
        return render_template("remove.html", user=session['username'],
                               result=1, display="Success!", stockRslt=getStock())

# Add user page
@app.route('/adduser', methods = ['GET', 'POST'])
def adduser():

    if 'username' not in session:
        # Not logged_in. Redirect to login page.
        return render_template('login.html')

    if request.method == 'GET':
        return render_template("adduser.html", user=session['username'],
                               result=0, display='')
    else:
        # Get the username, password and the teamname of the new user.
        get_un = request.form['get_un']
        get_pswd = request.form['get_pswd']
        get_tn = request.form['get_tn']

        # Insert the new user to the list of Users.
        exec_commit("Insert into Users VALUES ('%s', '%s', '%s');"
                    % (get_un, get_pswd, get_tn))

        # Success. Stays on the same page and resets the form.
        return render_template("adduser.html", user=session['username'],
                               result=1, display='Success!')

'''
Helper methods
'''

# Executes the query passed via argument and
# returns the result from executing the query on the database.
def getQueryResult(query):
    # Connect to the database
    conn = sqlite3.connect('Inventory.db')
    cur = conn.cursor()
    rslt = cur.execute(query).fetchall()
    return rslt

# Execute a query passed via argument and commit the change to the database.
def exec_commit(query):
    # Connect to the database
    conn = sqlite3.connect('Inventory.db')
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    return "Done"

# Returns the contents of the Stock table from the database.
def getStock():
    return getQueryResult("Select * from Stock ORDER BY ID;")

# Generates a new ID for a new item and returns it.
def getNewID():
    maxID = 0
    for rslt in getStock():
        if (maxID < rslt[0]):
            maxID = rslt[0]
    return maxID + 1

# Get the number of Units available for a given item.
def getUnitsAvail(query):
    units = -1
    for rslt in getQueryResult(query):
        if (units < rslt[1]):
            units = rslt[1]
    return units

# Returns the contents of the ItemsUsed table from the database.
def getInUse():
    return getQueryResult("Select i.ID, s.TechName, i.UnitsUsed, i.UsedIn, i.UsedBy \
                            from ItemsUsed i, Stock s WHERE s.ID = i.ID ORDER BY i.id;")




if __name__ == "__main__":
    app.run(debug=True)
