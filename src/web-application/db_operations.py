import pymysql

def create_connection():
    connection = pymysql.connect(
        user='root',
        password='Incorrect',  # Change this to your MySQL password
        host='localhost',
        cursorclass=pymysql.cursors.DictCursor
    )

    # Create database if it doesn't exist
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS users")
    
    # Switch to the 'users' database
    connection.select_db('users')

    # Create the 'users' table if it doesn't exist
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                public_key TEXT,
                private_key TEXT
            )
        ''')

    return connection

def create_user(conn, user_info):
    sql = ''' INSERT INTO users(username, first_name, last_name, public_key, private_key)
              VALUES(%s,%s,%s,%s,%s) '''
    with conn.cursor() as cursor:
        cursor.execute(sql, user_info)
        conn.commit()

def get_user_by_username(conn, username):
    sql = "SELECT * FROM users WHERE username=%s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (username,))
        rows = cursor.fetchall()
        return rows

