import os
import sys
import sqlite3

def get_db_path():
    """
    إرجاع مسار قاعدة البيانات الصحيح بشكل ديناميكي:
    - يعمل أثناء التطوير (Development)
    - يعمل بعد التجميع كملف تنفيذي EXE (PyInstaller)
    """
    if getattr(sys, 'frozen', False):
        # المسار عند تشغيل التطبيق كملف EXE (بجانب الملف التنفيذي)
        base_dir = os.path.dirname(sys.executable)
    else:
        # المسار أثناء التطوير
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_dir, 'supermarket.db')

def get_connection():
    """
    إرجاع اتصال جاهز بقاعدة البيانات SQLite
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    # تفعيل دعم المفاتيح الأجنبية لتحسين سلامة البيانات
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn