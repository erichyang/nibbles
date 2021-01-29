import sqlite3

conn = sqlite3.connect('user.db')
c = conn.cursor()

# Create a Table
# c.execute("""CREATE TABLE users (
#         user_id integer primary key,
#         pts integer,
#         bal integer,
#         time text,
#         description text
#     )""")


conn.commit()
conn.close()

# conn = sqlite3.connect('gacha.db')
# c = conn.cursor()
#
# # Create a Table
# c.execute("""CREATE TABLE users (
#         user_id integer primary key,
#         event_guarantee integer,
#         event_pity5 integer,
#         reg_pity5 integer,
#         event_pity4 integer,
#         reg_pity4 integer
#     )""")
#
# c.execute("""CREATE TABLE inventory (
#         user_id integer primary key,
#         characters text,
#         weapons text,
#         xp_books integer
#     )""")

# conn.commit()
# conn.close()

# import sqlite3

# Connect to database
# conn = sqlite3.connect('user.db')

# Create a cursor
# c = conn.cursor()

# Create a Table
# c.execute("""CREATE TABLE users (
#         user_id integer primary key,
#         pts integer,
#         bal integer
#     )""")

# Datatypes:
# NULL - exist or not?
# INTERGER - number
# REAL - decimals
# TEXT - string
# BLOB - stored as is, Ex: image, mp3 file

# Add one row
# c.execute("INSERT INTO users VALUES (123456789, 0, 0)")

# Add many row
# c.executemany("INSERT INTO users VALUES (?,?,?)", [(1, 2, 3), (4, 5, 6)])

# Update records
# c.execute("""UPDATE users SET pts = 2
#             WHERE user_id = 123456789
#    """)

# Delete Records
# c.execute("DELETE from users WHERE user_id = 123456789")
# c.execute("DELETE FROM users")

# Get Data
# c.execute("SELECT * FROM users")
# c.fetchone()
# c.fetchmany(3)
# c.fetchall()

# Find data
# num operators = < > <=
# text operators LIKE sta%
# c.execute("SELECT * FROM users WHERE pts = 0 AND/OR bal = 0")
# print(c.fetchall())

# sort data
# c.execute("SELECT * FROM users ORDER BY pts")
# top pts ppl
# descending
# c.execute("SELECT * FROM users ORDER BY pts DESC LIMIT 10")
# Commit our command
# conn.commit()
#
# Close our connection
# conn.close()
