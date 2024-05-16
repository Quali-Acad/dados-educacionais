import mysql.connector

class Conn:
    def __init__(self, username, password, host, database):
        self.conn = mysql.connector.connect(
            user=username,
            password=password,
            host=host,
            database=database
        )

        self.cursor = self.conn.cursor()

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def execute_query(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_insert(self, query, params=None):
        self.cursor.execute(query, params)
        self.conn.commit()
