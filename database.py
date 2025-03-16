import sqlite3

def execute_query(query,values):
    connection = sqlite3.connect("badmintonbank.db")
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    connection.close()

def execute_select_query(query, values):
    connection = sqlite3.connect("badmintonbank.db")
    cursor = connection.cursor()
    data = cursor.execute(query, values).fetchall()
    connection.close()
    return data
