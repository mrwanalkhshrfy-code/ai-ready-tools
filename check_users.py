import sqlite3
import os
import db_config
# current_dir = os.path.dirname(os.path.abspath(__file__))
# db_path = os.path.join(current_dir, 'supermarket.db')
from db_config import get_db_path, get_connection

try:
    conn = sqlite3.connect(db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role FROM Users")
    users = cursor.fetchall()
    
    print("\n--- قائمة المستخدمين المسجلين في النظام ---")
    if not users:
        print("❌ قاعدة البيانات فارغة! لا يوجد أي مستخدم مسجل.")
    else:
        for user in users:
            print(f"اسم المستخدم: {user[0]} | كلمة المرور: {user[1]} | الصلاحية: {user[2]}")
    print("-------------------------------------------\n")
    
    conn.close()
except Exception as e:
    print(f"حدث خطأ: {e}")