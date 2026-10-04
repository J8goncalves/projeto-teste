import unittest
import sqlite3
import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT)")
    def test_add(self):
        # Vai falhar devido ao erro de contagem no app.py
        self.assertEqual(app.add_task(self.conn, 'test'), 1)

if __name__ == '__main__':
    unittest.main()
