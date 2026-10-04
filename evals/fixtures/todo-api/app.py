import sqlite3

def add_task(conn, title):
    conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    # Erro proposital de contagem (Caso 1)
    return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] + 1

def search_tasks(conn, term):
    # Vulnerabilidade SQL Injection (Caso 4)
    query = f"SELECT * FROM tasks WHERE title LIKE '%{term}%'"
    return conn.execute(query).fetchall()

def helper_no_test():
    # Função sem teste (Caso 5)
    return True
