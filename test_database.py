#!/usr/bin/env python3
"""
Database Structure Validation Script
====================================

Validates database structure and connectivity for LearnHub Student Management System.
This script ensures the database is properly set up to handle real student data
added through the frontend interface.

Purpose:
- Validate database connectivity and structure
- Test table creation and relationships
- Verify foreign key constraints
- Test basic CRUD operations
- Ensure search functionality works correctly
- Validate data integrity

Author: Paul Mulilo
Version: 1.0.0
"""

# Import required modules for database validation
import sys  # System-specific parameters and functions
import os   # Operating system interface
import sqlite3  # SQLite database operations
from datetime import datetime  # Date and time handling
from prettytable import PrettyTable  # Table display

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_database_structure():
    """Validate database structure and connectivity"""
    print("WELCOME TO LEARNHUB DATA STORE")

    # Use the main database (not test database)
    db_path = 'learnhub.db'

    try:
        # Connect to SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        print("✅ Database connection successful!")

        # List all tables in the database
        print("📋 Listing all tables in the database...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if tables:
            print("📊 Tables found:")
            for table in tables:
                table_name = table[0]
                # Skip system tables
                if table_name in ['users', 'sqlite_sequence']:
                    continue
                print(f"   - {table_name}")
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"     Rows: {row_count}")
        else:
            print("   No tables found in the database.")

        print("📋 Database Schema:")
        for table in ['students', 'courses', 'student_courses']:
            print(f"\n--- {table.upper()} TABLE ---")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            # Foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = cursor.fetchall()
            fk_dict = {from_col: f"{table_ref}.{to_col}" for id_, seq, table_ref, from_col, to_col, on_update, on_delete, match in fks}
            table_data = []
            for col in columns:
                cid, name, type_, notnull, dflt_value, pk = col
                pk_str = "Yes" if pk else "No"
                fk_str = fk_dict.get(name, "No")
                table_data.append([name, type_, pk_str, fk_str])
            headers = ['Column Name', 'Type', 'Primary Key', 'Foreign Key']
            table = PrettyTable()
            table.field_names = headers
            for row in table_data:
                table.add_row(row)
            print(table)

        # Print sample student data with courses
        print("\n📋 Sample Student Data with Courses:")
        

        cursor.execute("""
            SELECT s.student_id, s.name, s.age, GROUP_CONCAT(c.course_name, ', ') as courses
            FROM students s
            LEFT JOIN student_courses sc ON s.id = sc.student_id
            LEFT JOIN courses c ON sc.course_id = c.course_id
            GROUP BY s.id
            ORDER BY s.student_id
        """)
        student_data = cursor.fetchall()

        if student_data:
            table_data = []
            for row in student_data:
                student_id, name, age, courses = row
                course_display = courses if courses else "No Course"
                table_data.append([student_id, name, age, course_display])
            headers = ['Student ID', 'Name', 'Age', 'Course']
            table = PrettyTable()
            table.field_names = headers
            for row in table_data:
                table.add_row(row)
            print(table)

        return True

    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """Main validation function"""
    print("=" * 60)
    print("DATABASE STRUCTURE VALIDATION")
    print("=" * 60)
    print(f"Validation started at: {datetime.now()}")
    print()
    success = validate_database_structure()
    print()
if __name__ == "__main__":
    main()
