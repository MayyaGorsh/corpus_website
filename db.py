import mysql.connector

config = {
    "host": "",
    "user": "",
    "password": "",
    "database": ""
}

def query_db(sql_request, params=None):
    cnx = mysql.connector.connect(**config)
    cur = cnx.cursor(dictionary=True)
    cur.execute(sql_request, params or ())
    result = cur.fetchall()
    cur.close()
    cnx.close()
    return result

