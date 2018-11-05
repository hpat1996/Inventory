# A program to create the tables for the inventory database.
# There are 4 tables to store the data in the inventory.

# Table Stock
#    ID of an item
#    Technical Name of the item
#    Units already in use
#    Units available in the inventory
#    The description of the item
#    The person who made the last update
# The units available and in use cannot be negative

# Table Tags
#    ID of the item
#    The tags of the item
# The ID of the item here is the same as the ID in the Stock table

# Table ItemsUsed
#    ID of the item
#    The number of units of the item in use
#    The place where the item is being used
#    The person who borrowed it
# The ID of the item here is the same as the ID in the Stock table

# Table Users
#    The username for the user
#    The password for the user
#    The TeamName for the user

import sqlite3

# Create a connection with the database
conn = sqlite3.connect('Inventory.db')

# cur is used to talk to the database
# cur.execute(Query) will execute queries
cur = conn.cursor()

# Creates a table Stock which stores the details of an item:
# ID, TechName, UnitsUsed, UnitsAvail, Description, LastUpdated
cur.execute("Create Table Stock(" +
                        "ID INT PRIMARY KEY, " +
                        "TechName VARCHAR(100) NOT NULL, " +
                        "UnitsUsed INT NOT NULL, " +
                        "UnitsAvail INT NOT NULL, " +
                        "Description VARCHAR(500) NOT NULL, " +
                        "LastUpdated VARCHAR(100) NOT NULL "
                        "CHECK(UnitsAvail >= 0 AND UnitsUsed >= 0));")

# Creates a table Tags which stores the tags for each item:
# ID, Tag
cur.execute("Create Table Tags(" +
                        "ID  INT, " +
                        "Tag VARCHAR(100) NOT NULL, " +
                        "FOREIGN KEY (ID) REFERENCES Stock(ID));")

# Creates a table ItemUsed which stores where the used items have been used:
# ID, UnitsUsed, UsedIn, UsedBy
cur.execute("Create Table ItemsUsed(" +
                        "ID INT, " +
                        "UnitsUsed INT NOT NULL, " +
                        "UsedIn VARCHAR(200) NOT NULL, " +
                        "UsedBy VARCHAR(100) NOT NULL, " +
                        "FOREIGN KEY(ID) REFERENCES Stock(ID));")

conn.commit()

# Creates a table Users which stores the login credentials for the users:
# username, password, TeamName
cur.execute("Create Table Users(" +
            "username VARCHAR(100) PRIMARY KEY, " +
            "password VARCHAR(100) NOT NULL, " +
            "TeamName VARCHAR(100) NOT NULL);")
conn.commit()


cur.execute("Insert into Users VALUES ('admin', 'UWHLadmin_123', 'ADMINISTRATOR');");
conn.commit()

# Prints a success message
# if the table is created successfully within the database
print "Database Created and Tables inserted."
print "Success!"
