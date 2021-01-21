import sqlite3

conn = sqlite3.connect('user.db')
c = conn.cursor()

# Create a Table
# c.execute("""CREATE TABLE users (
#         user_id integer primary key,
#         pts integer,
#         bal integer
#     )""")


c.execute("""CREATE TABLE summons (
         user_id integer primary key,
         pity integer,
         characters text
     )""")

conn.commit()
conn.close()