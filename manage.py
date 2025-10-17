"""
LearnHub - Student Management System
====================================

A comprehensive Flask-based web application for managing student information,
courses, and academic records. This application provides a complete solution
for educational institutions to track students, manage course enrollments,
and perform advanced search operations.

Main Features:
- Student CRUD operations (Create, Read, Update, Delete)
- Course management and enrollment tracking
- Advanced search with filters and live results
- Session-based recent activity tracking
- Data export capabilities (CSV)
- Responsive web interface
- RESTful API endpoints

Author: Paul Mulilo
Version: 1.0.0
"""

# Import required modules for the Flask application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import re  # Regular expressions for email validation
from datetime import datetime, timedelta  # Date/time handling and session management
import json  # JSON data handling
import os  # For environment variables
from models import db, Student, Course, student_courses
import csv
import io
import sqlite3  # SQLite database module

# Initialize Flask application with custom template and static folders
app = Flask(__name__,
           template_folder='frontend/Pages',  # HTML templates location
           static_folder='frontend/static')   # CSS, JS, images location

# Application security configuration - Use environment variable in production
app.secret_key = os.environ.get('SECRET_KEY', 'L8AR9NHUB')  # Use env var for production
app.permanent_session_lifetime = timedelta(minutes=10)  # Session lasts 10 minutes

# Database configuration - Use environment variable for database path
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(os.getcwd(), "learnhub.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

def create_connection():
    """Create a database connection to the SQLite database"""
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(), "learnhub.db"))
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def seed_test_data():
    """Seed test data using SQLAlchemy"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()

            # Check if data already exists
            if Student.query.count() > 0:
                print("Test data already exists!")
                return

            # Insert test students
            test_students = [
                ("2431210033", "Paul Mulilo", 30, "mulilopaul@gmail.com"),
                ("2431210038", "Margaret Nsamu", 28, "maggiensamu@gmail.com"),
                ("2431210046", "Lishomwa Mubita", 22, "lishomwamubita@gmail.com"),
                ("2431210088", "Natasha Butabwan'gombe", 23, "natashaba2gmail.com"),
                ("2431210087", "Heremin Kasongo", 23, "kasongoheremin@gmail.com"),
                ("2431210055", "Diana Prince", 21, "dianap@gmail.com"),
            ]

            # Insert test courses
            test_courses = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "English", "History"]
            course_objects = []
            for course_name in test_courses:
                course = Course.query.filter_by(course_name=course_name).first()
                if not course:
                    course = Course(course_name=course_name)
                    db.session.add(course)
                    course_objects.append(course)
                else:
                    course_objects.append(course)

            db.session.commit()

            # Create students and link to courses
            for i, (student_id_val, name, age, email) in enumerate(test_students):
                student = Student(student_id=student_id_val, name=name, age=age, email=email)
                db.session.add(student)
                db.session.commit()  # Commit to get student.id

                # Link to some courses (example relationships)
                if i < len(course_objects):
                    student.courses.append(course_objects[i])
                    if i + 1 < len(course_objects):
                        student.courses.append(course_objects[i + 1])

            db.session.commit()
            print("Test data seeded successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"Error seeding test data: {e}")

# Password helpers
def hash_password(password):
    pass

def check_password(password, hashed):
    pass

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# ---------------- Session-based Recent Students Management ---------------- #

def get_recent_students_from_session():
    """Get recent students from session storage"""
    if 'recent_students' not in session:
        session['recent_students'] = []
    return session['recent_students']

def add_student_to_session(student_data):
    """Add a student to session storage as recent student"""
    recent_students = get_recent_students_from_session()

    # Create student entry with timestamp
    student_entry = {
        'id': student_data['id'],
        'student_id': student_data['student_id'],
        'name': student_data['name'],
        'email': student_data['email'],
        'courses': student_data.get('courses', 'No courses'),
        'activity_type': student_data.get('activity_type', 'Added'),
        'activity_date': student_data.get('activity_date', datetime.now().isoformat()),
        'session_id': student_data.get('session_id', str(student_data['id']))
    }

    # Remove existing entry for this student if it exists
    recent_students = [s for s in recent_students if s['session_id'] != student_entry['session_id']]

    # Add new entry at the beginning
    recent_students.insert(0, student_entry)

    # Keep only the last 10 recent students
    session['recent_students'] = recent_students[:10]

    # Mark session as modified
    session.modified = True

def clear_session_recent_students():
    """Clear all recent students from session"""
    if 'recent_students' in session:
        session.pop('recent_students', None)
        session.modified = True

def initialize_session():
    """Initialize session with empty recent students if not exists"""
    if 'recent_students' not in session:
        session['recent_students'] = []
        session.modified = True

# ---------------- Dashboard / Index ---------------- #

@app.route('/')
def index():
    """When app runs, show index.html instead of dashboard"""
    return render_template('index.html')

# ---------------- Student Management ---------------- #

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    """
    Handle student addition with comprehensive validation

    Validates:
    - Student ID must be a positive integer
    - All required fields must be filled
    - Email format validation
    - Duplicate checking for student_id and email
    - Age must be a positive integer
    """
    if request.method == 'POST':
        # Get form data
        student_id_str = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        age_str = request.form.get('age', '').strip()
        email = request.form.get('email', '').strip()
        courses_str = request.form.get('courses', '').strip()

        # Comprehensive validation
        errors = []

        # Validate student ID is integer
        try:
            student_id = int(student_id_str)
            if student_id <= 0:
                errors.append('Student ID must be a positive integer!')
            elif student_id >= 9000000000:
                errors.append('Student ID must be less than 9,000,000,000!')
        except ValueError:
            errors.append('Student ID must be a valid integer!')

        # Validate name
        if not name:
            errors.append('Name is required!')
        elif len(name) < 2:
            errors.append('Name must be at least 2 characters long!')
        elif len(name) > 100:
            errors.append('Name must be less than 100 characters!')

        # Validate age
        try:
            age = int(age_str)
            if age <= 0:
                errors.append('Age must be a positive integer!')
            elif age > 150:
                errors.append('Age must be realistic (less than 150)!')
        except ValueError:
            errors.append('Age must be a valid integer!')

        # Validate email
        if not email:
            errors.append('Email is required!')
        elif not validate_email(email):
            errors.append('Please enter a valid email address!')
        elif len(email) > 255:
            errors.append('Email must be less than 255 characters!')

        # Validate courses (optional but clean if provided)
        courses = []
        if courses_str:
            courses = [course.strip() for course in courses_str.split(',') if course.strip()]
            if len(courses) > 10:
                errors.append('Maximum 10 courses allowed!')
            for course in courses:
                if len(course) > 100:
                    errors.append('Course names must be less than 100 characters!')

        # If there are validation errors, show them
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add.html')

        try:
            # Check for duplicate student_id
            if Student.query.filter_by(student_id=student_id).first():
                flash('Student ID already exists!', 'error')
                return render_template('add.html')

            # Check for duplicate email
            if Student.query.filter_by(email=email).first():
                flash('Email already exists!', 'error')
                return render_template('add.html')

            # Create student
            student = Student(student_id=student_id, name=name, age=age, email=email)
            db.session.add(student)
            db.session.commit()  # To get student.id

            # Add courses
            for course_name in courses:
                course_name = course_name.strip()
                if not course_name:
                    continue
                # Check if course exists
                course = Course.query.filter_by(course_name=course_name).first()
                if not course:
                    course = Course(course_name=course_name)
                    db.session.add(course)
                    db.session.commit()  # To get course.course_id
                # Link student and course
                student.courses.append(course)

            db.session.commit()

            # Add student to session storage for recent students
            student_data = {
                'id': student.id,
                'student_id': student_id,
                'name': name,
                'email': email,
                'courses': ', '.join(courses) if courses else 'No courses',
                'activity_type': 'Added',
                'activity_date': datetime.now().isoformat(),
                'session_id': str(student.id)
            }
            add_student_to_session(student_data)

            flash('Student added successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Error adding student: ' + str(e), 'error')
            print(f"Database error: {e}")

    return render_template('add.html')

@app.route('/view')
def view():
    try:
        # Fetch all students with their courses
        students_query = Student.query.order_by(Student.name).all()
        students = []
        for student in students_query:
            student_dict = {
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'age': student.age,
                'email': student.email,
                'courses': [course.course_name for course in student.courses]
            }
            students.append(student_dict)

        total_students = Student.query.count()

    except Exception as e:
        print(f"Database error: {e}")
        students = []
        total_students = 0

    return render_template('view.html', students=students, total_students=total_students)

@app.route('/view_student/<int:student_id>')
def view_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        courses = [course.course_name for course in student.courses]

        # Convert student object to tuple format for template compatibility
        student_data = (
            student.id,
            student.student_id,
            student.name,
            student.age,
            student.email,
            student.created_at,
            student.updated_at
        )

        return render_template('view_student.html', student=student_data, courses=courses)

    except Exception as e:
        print(f"Database error: {e}")
        flash('Student not found!', 'error')
        return redirect(url_for('view'))

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)

        if request.method == 'POST':
            student_id_val = request.form['student_id']
            name = request.form['name']
            age = request.form['age']
            courses_str = request.form.get('courses', '').strip()
            courses_list = [course.strip() for course in courses_str.split(',') if course.strip()]
            email = request.form['email']

            # Check for duplicate student_id (excluding current student)
            existing_student = Student.query.filter_by(student_id=student_id_val).first()
            if existing_student and existing_student.id != student_id:
                flash('Student ID already exists!', 'error')
                # Convert student object to tuple for template compatibility
                student_data = (
                    student.id, student.student_id, student.name, student.age, student.email,
                    student.created_at, student.updated_at
                )
                courses = [course.course_name for course in student.courses]
                return render_template('edits.html', student=student_data, courses=courses)

            # Check for duplicate email (excluding current student)
            existing_email = Student.query.filter_by(email=email).first()
            if existing_email and existing_email.id != student_id:
                flash('Email already exists!', 'error')
                # Convert student object to tuple for template compatibility
                student_data = (
                    student.id, student.student_id, student.name, student.age, student.email,
                    student.created_at, student.updated_at
                )
                courses = [course.course_name for course in student.courses]
                return render_template('edits.html', student=student_data, courses=courses)

            # Update student info
            student.student_id = student_id_val
            student.name = name
            student.age = age
            student.email = email
            student.updated_at = datetime.utcnow()

            # Clear existing course relationships
            student.courses.clear()

            # Add new courses
            for course_name in courses_list:
                course_name = course_name.strip()
                if not course_name:
                    continue
                # Check if course exists
                course = Course.query.filter_by(course_name=course_name).first()
                if not course:
                    course = Course(course_name=course_name)
                    db.session.add(course)
                # Link student and course
                student.courses.append(course)

            db.session.commit()

            # Add updated student to session storage for recent students
            student_data = {
                'id': student.id,
                'student_id': student_id_val,
                'name': name,
                'email': email,
                'courses': ', '.join(courses_list) if courses_list else 'No courses',
                'activity_type': 'Updated',
                'activity_date': datetime.now().isoformat(),
                'session_id': str(student.id)
            }
            add_student_to_session(student_data)

            flash('Student updated successfully!', 'success')
            return redirect(url_for('view'))

        # GET request - fetch student data for editing
        # Convert student object to tuple for template compatibility
        student_data = (
            student.id, student.student_id, student.name, student.age, student.email,
            student.created_at, student.updated_at
        )
        courses = [course.course_name for course in student.courses]

        return render_template('edits.html', student=student_data, courses=courses)

    except Exception as e:
        db.session.rollback()
        flash('Error updating student: ' + str(e), 'error')
        print(f"Database error: {e}")
        return redirect(url_for('view'))

@app.route('/delete/<int:student_id>')
def delete_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)

        # Remove student from session if present
        recent_students = get_recent_students_from_session()
        recent_students = [s for s in recent_students if s['id'] != student_id]
        session['recent_students'] = recent_students
        session.modified = True

        # Delete the student
        db.session.delete(student)
        db.session.commit()

        flash('Student deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Error deleting student: ' + str(e), 'error')
        print(f"Database error: {e}")

    return redirect(url_for('view'))

@app.route('/search', methods=['GET', 'POST'])
def search_students():
    if request.method == 'POST':
        query = request.form['query']
        connection = create_connection()
        results = []
        if connection:
            cursor = connection.cursor()
            try:
                # Search across students and their courses
                search_query = """
                SELECT DISTINCT s.id, s.student_id, s.name, s.age, s.email, s.created_at
                FROM students s
                LEFT JOIN student_courses sc ON s.id = sc.student_id
                LEFT JOIN courses c ON sc.course_id = c.course_id
                WHERE s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR c.course_name LIKE ?
                ORDER BY s.name
                """
                search_term = '%' + query + '%'
                cursor.execute(search_query, (search_term, search_term, search_term, search_term))
                results = cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Database error: {e}")
            finally:
                cursor.close()
                connection.close()

            return render_template('search.html', results=results, query=query)

    return render_template('search.html')

@app.route("/api/search_json")
def search_json():
    query = request.args.get("q", "").strip()
    results = []

    if query:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    SELECT DISTINCT s.id, s.name, s.email,
                           GROUP_CONCAT(c.course_name, ', ') as courses
                    FROM students s
                    LEFT JOIN student_courses sc ON s.id = sc.student_id
                    LEFT JOIN courses c ON sc.course_id = c.course_id
                    WHERE s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR c.course_name LIKE ?
                    GROUP BY s.id, s.name, s.email
                    LIMIT 10
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "courses": row[3] if row[3] else "No courses"
                    })
            except sqlite3.Error as e:
                print(f"Database error: {e}")
            finally:
                cursor.close()
                connection.close()

    return jsonify(results)
@app.route('/api/search')
def api_search_students():
    """API endpoint for live search functionality - Optimized for instant results"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 1:  # Reduced to 1 character for instant results
        return jsonify({'results': [], 'total': 0})

    connection = create_connection()
    results = []
    if connection:
        cursor = connection.cursor()
        try:
            # Optimized search query using indexes - search in order of relevance
            search_query = """
                SELECT DISTINCT s.id, s.student_id, s.name, s.age, s.email, s.created_at,
                       GROUP_CONCAT(c.course_name, ', ') as courses
                FROM students s
                LEFT JOIN student_courses sc ON s.id = sc.student_id
                LEFT JOIN courses c ON sc.course_id = c.course_id
                WHERE s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR c.course_name LIKE ?
                GROUP BY s.id, s.student_id, s.name, s.age, s.email, s.created_at
                ORDER BY
                    CASE
                        WHEN s.name LIKE ? THEN 1  -- Exact name matches first
                        WHEN s.student_id LIKE ? THEN 2  -- Student ID matches second
                        WHEN s.email LIKE ? THEN 3  -- Email matches third
                        WHEN c.course_name LIKE ? THEN 4  -- Course matches last
                        ELSE 5
                    END,
                    s.name  -- Alphabetical order within relevance groups
                LIMIT 15  -- Reduced limit for faster response
            """

            search_term = '%' + query + '%'
            exact_term = query + '%'  # For starts-with matching

            cursor.execute(search_query, (
                search_term, search_term, search_term, search_term,  # WHERE conditions
                exact_term, exact_term, exact_term, exact_term     # ORDER BY conditions
            ))
            rows = cursor.fetchall()

            # Format results with highlighting
            for row in rows:
                result = {
                    'id': row[0],
                    'student_id': row[1],
                    'name': row[2],
                    'age': row[3],
                    'email': row[4],
                    'created_at': row[5],
                    'courses': row[6] if row[6] else 'No courses'
                }
                results.append(result)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return jsonify({'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({'results': results, 'total': len(results), 'query': query})

@app.route('/api/search/advanced')
def api_advanced_search():
    """API endpoint for advanced search with filters"""
    # Get query parameters
    query = request.args.get('q', '').strip()
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    courses = request.args.getlist('courses')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    connection = create_connection()
    results = []
    if connection:
        cursor = connection.cursor()
        try:
            # Build dynamic query
            base_query = """
                SELECT DISTINCT s.id, s.student_id, s.name, s.age, s.email, s.created_at,
                       GROUP_CONCAT(c.course_name, ', ') as courses
                FROM students s
                LEFT JOIN student_courses sc ON s.id = sc.student_id
                LEFT JOIN courses c ON sc.course_id = c.course_id
            """

            conditions = []
            params = []

            # Text search condition
            if query:
                conditions.append("(s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR c.course_name LIKE ?)")
                search_term = '%' + query + '%'
                params.extend([search_term, search_term, search_term, search_term])

            # Age range conditions
            if age_min is not None:
                conditions.append("s.age >= ?")
                params.append(age_min)

            if age_max is not None:
                conditions.append("s.age <= ?")
                params.append(age_max)

            # Course filter
            if courses:
                course_conditions = []
                for course in courses:
                    course_conditions.append("c.course_name LIKE ?")
                    params.append('%' + course + '%')
                conditions.append("(" + " OR ".join(course_conditions) + ")")

            # Add WHERE clause if conditions exist
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            # Add GROUP BY
            base_query += " GROUP BY s.id, s.student_id, s.name, s.age, s.email, s.created_at"

            # Add sorting
            valid_sort_fields = ['name', 'student_id', 'age', 'created_at']
            if sort_by in valid_sort_fields:
                order = "DESC" if sort_order.lower() == 'desc' else "ASC"
                base_query += f" ORDER BY s.{sort_by} {order}"

            # Add pagination
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # Execute query
            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            # Format results
            for row in rows:
                result = {
                    'id': row[0],
                    'student_id': row[1],
                    'name': row[2],
                    'age': row[3],
                    'email': row[4],
                    'created_at': row[5],
                    'courses': row[6] if row[6] else 'No courses'
                }
                results.append(result)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return jsonify({'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({'results': results, 'total': len(results)})

@app.route('/api/search/history', methods=['GET', 'POST', 'DELETE'])
def api_search_history():
    """API endpoint for search history management"""
    if request.method == 'POST':
        # Add search to history
        search_data = request.get_json()
        if not search_data or 'query' not in search_data:
            return jsonify({'error': 'Query is required'}), 400

        # In a real app, you'd store this in a database
        # For now, we'll use session storage
        if 'search_history' not in session:
            session['search_history'] = []

        search_history = session['search_history']

        # Remove existing entry if it exists
        search_history = [s for s in search_history if s['query'] != search_data['query']]

        # Add new entry at the beginning
        search_entry = {
            'query': search_data['query'],
            'timestamp': datetime.now().isoformat(),
            'filters': search_data.get('filters', {})
        }
        search_history.insert(0, search_entry)

        # Keep only last 10 searches
        session['search_history'] = search_history[:10]
        session.modified = True

        return jsonify({'success': True, 'search_history': session['search_history']})

    elif request.method == 'DELETE':
        # Clear search history
        if 'search_history' in session:
            session.pop('search_history', None)
            session.modified = True
        return jsonify({'success': True})

    else:
        # Get search history
        search_history = session.get('search_history', [])
        return jsonify({'search_history': search_history})

@app.route('/api/search/export')
def api_export_search():
    """API endpoint for exporting search results"""
    format_type = request.args.get('format', 'csv')
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = connection.cursor()
    try:
        # Get all matching students (no limit for export)
        search_query = """
            SELECT DISTINCT s.id, s.student_id, s.name, s.age, s.email, s.created_at,
                   GROUP_CONCAT(c.course_name, ', ') as courses
            FROM students s
            LEFT JOIN student_courses sc ON s.id = sc.student_id
            LEFT JOIN courses c ON sc.course_id = c.course_id
            WHERE s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR c.course_name LIKE ?
            GROUP BY s.id, s.student_id, s.name, s.age, s.email, s.created_at
            ORDER BY s.name
        """

        search_term = '%' + query + '%'
        cursor.execute(search_query, (search_term, search_term, search_term, search_term))
        rows = cursor.fetchall()

        if format_type.lower() == 'csv':
            # Generate CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(['Student ID', 'Name', 'Age', 'Email', 'Courses', 'Created At'])

            # Write data
            for row in rows:
                writer.writerow([
                    row[1],  # student_id
                    row[2],  # name
                    row[3],  # age
                    row[4],  # email
                    row[6] if row[6] else 'No courses',  # courses
                    row[5]   # created_at
                ])

            csv_data = output.getvalue()
            output.close()

            response = jsonify({'data': csv_data, 'filename': f'search_results_{query[:20]}.csv'})
            response.headers['Content-Type'] = 'application/json'
            return response

        else:
            return jsonify({'error': 'Unsupported format'}), 400

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/search/bulk-actions', methods=['POST'])
def api_bulk_actions():
    """API endpoint for bulk operations on search results"""
    data = request.get_json()
    if not data or 'action' not in data or 'student_ids' not in data:
        return jsonify({'error': 'Action and student_ids are required'}), 400

    action = data['action']
    student_ids = data['student_ids']

    if not student_ids:
        return jsonify({'error': 'No students selected'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = connection.cursor()
    try:
        if action == 'delete':
            # Delete selected students
            placeholders = ','.join(['?'] * len(student_ids))
            cursor.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
            connection.commit()

            return jsonify({
                'success': True,
                'message': f'Successfully deleted {len(student_ids)} students',
                'deleted_count': len(student_ids)
            })

        elif action == 'export':
            # Export selected students
            placeholders = ','.join(['?'] * len(student_ids))
            cursor.execute(f"""
                SELECT s.id, s.student_id, s.name, s.age, s.email, s.created_at,
                       GROUP_CONCAT(c.course_name, ', ') as courses
                FROM students s
                LEFT JOIN student_courses sc ON s.id = sc.student_id
                LEFT JOIN courses c ON sc.course_id = c.course_id
                WHERE s.id IN ({placeholders})
                GROUP BY s.id, s.student_id, s.name, s.age, s.email, s.created_at
                ORDER BY s.name
            """, student_ids)

            rows = cursor.fetchall()

            # Generate CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Student ID', 'Name', 'Age', 'Email', 'Courses', 'Created At'])

            for row in rows:
                writer.writerow([
                    row[1], row[2], row[3], row[4],
                    row[6] if row[6] else 'No courses', row[5]
                ])

            csv_data = output.getvalue()
            output.close()

            return jsonify({
                'success': True,
                'data': csv_data,
                'filename': f'selected_students_{len(student_ids)}_items.csv'
            })

        else:
            return jsonify({'error': 'Unsupported action'}), 400

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/recent_students')
def api_recent_students():
    """API endpoint for fetching recently added/edited students"""
    connection = create_connection()
    recent_students = []
    if connection:
        cursor = connection.cursor()
        try:
            # Fetch students ordered by most recent activity (using created_at since updated_at doesn't exist)
            recent_query = """
                SELECT s.id, s.student_id, s.name, s.email, s.created_at,
                       GROUP_CONCAT(c.course_name, ', ') as courses,
                       'Added' as activity_type,
                       s.created_at as last_activity
                FROM students s
                LEFT JOIN student_courses sc ON s.id = sc.student_id
                LEFT JOIN courses c ON sc.course_id = c.course_id
                GROUP BY s.id, s.student_id, s.name, s.email, s.created_at
                ORDER BY last_activity DESC
                LIMIT 10
            """
            cursor.execute(recent_query)
            rows = cursor.fetchall()

            # Format results
            for row in rows:
                student = {
                    'id': row[0],
                    'student_id': row[1],
                    'name': row[2],
                    'email': row[3],
                    'courses': row[5] if row[5] else 'No courses',
                    'activity_type': row[6],
                    'activity_date': row[7]
                }
                recent_students.append(student)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return jsonify({'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({'recent_students': recent_students})

@app.route('/api/check_duplicate')
def api_check_duplicate():
    """API endpoint for checking duplicates"""
    field_type = request.args.get('type')
    value = request.args.get('value', '').strip()
    exclude_id = request.args.get('exclude_id')

    if not field_type or not value:
        return jsonify({'error': 'Missing parameters'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = connection.cursor()
    try:
        if field_type == 'student_id':
            query = "SELECT COUNT(*) FROM students WHERE student_id = ?"
            params = (value,)
            if exclude_id:
                query += " AND id != ?"
                params = (value, int(exclude_id))

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return jsonify({'is_duplicate': count > 0})

        elif field_type == 'email':
            query = "SELECT COUNT(*) FROM students WHERE email = ?"
            params = (value,)
            if exclude_id:
                query += " AND id != ?"
                params = (value, int(exclude_id))

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return jsonify({'is_duplicate': count > 0})

        else:
            return jsonify({'error': 'Invalid field type'}), 400

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    # Initialize session if needed
    initialize_session()

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT course_id) FROM student_courses")
            active_courses = cursor.fetchone()[0]

            cursor.execute("""
                SELECT AVG(course_count)
                FROM (
                    SELECT COUNT(sc.course_id) as course_count
                    FROM students s
                    LEFT JOIN student_courses sc ON s.id = sc.student_id
                    GROUP BY s.id
                )
            """)
            result = cursor.fetchone()
            avg_courses_per_student = round(result[0], 1) if result and result[0] else 0

            # Get recent students from session instead of database
            recent_students = get_recent_students_from_session()

        except sqlite3.Error as e:
            total_students = active_courses = avg_courses_per_student = 0
            recent_students = []
            print(f"Database error: {e}")
        finally:
            cursor.close()
            connection.close()

        return render_template('dashboard.html',
                             total_students=total_students,
                             active_courses=active_courses,
                             avg_courses_per_student=avg_courses_per_student,
                             recent_students=recent_students)

    return render_template('dashboard.html',
                         total_students=5,
                         active_courses=0,
                         avg_courses_per_student=0,
                         recent_students=[])


if __name__ == "__main__":
    seed_test_data()
    # Bind to all network interfaces and use Render's provided PORT
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
