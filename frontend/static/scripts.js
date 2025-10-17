// scripts.js
// JavaScript functionality for LearnHub Student Management System
// ===============================================================
//
// This file contains all the frontend JavaScript functionality for the
// LearnHub Student Management System. It handles:
// - Live search functionality with AJAX
// - Form validation and submission
// - Modal management
// - Notification system
// - Dashboard interactions
// - Session management
// - Dynamic content updates
//
// Author: Paul Mulilo
// Version: 1.0.0

// =====================
// Notification System
// =====================
function showNotification(message, type = "success") {
  const notification = document.getElementById("notification");
  const messageElement = document.getElementById("notification-message");
  const icon = notification.querySelector("i");

  messageElement.textContent = message;
  notification.className = `notification ${type}`;

  if (type === "success") {
    icon.className = "fas fa-check-circle";
    notification.style.borderColor = "#06d6a0";
  } else {
    icon.className = "fas fa-exclamation-triangle";
    notification.style.borderColor = "#e63946";
  }

  notification.style.display = "block";
  setTimeout(() => {
    notification.style.display = "none";
  }, 3000);
}

// =====================
// Recent Students
// =====================
function setupRecentStudents() {
  const container = document.getElementById("recent-students-container");
  const loadingIndicator = document.getElementById("loading-indicator");
  if (container) fetchRecentStudents(container, loadingIndicator);
}

function fetchRecentStudents(container, loadingIndicator) {
  fetch("/api/recent_students")
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        container.innerHTML =
          '<div class="text-danger p-2">Error loading recent students.</div>';
        return;
      }

      const students = data.recent_students || [];
      if (students.length === 0) {
        container.innerHTML =
          '<div class="text-muted p-2">No recent students found.</div>';
        return;
      }

      container.innerHTML = students
        .map(
          (student) => `
        <div class="student-item">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h5 class="mb-0">${student.name}</h5>
              <span class="student-id">ID: ${student.student_id}</span>
              <span class="badge bg-${
                student.activity_type === "Added" ? "success" : "warning"
              } ms-2">
                ${student.activity_type}
              </span>
            </div>
            <div class="action-buttons">
              <button class="btn btn-sm btn-outline-primary" onclick="viewStudent(${student.id})">View</button>
              <button class="btn btn-sm btn-info" onclick="editStudent(${student.id})">Edit</button>
              <button class="btn btn-sm btn-danger delete-btn" onclick="deleteStudent(${student.id})">Delete</button>
            </div>
          </div>
          <p class="mt-2 mb-1"><strong>Email:</strong> ${student.email}</p>
          <div><strong>Courses:</strong> ${
            student.courses !== "No courses"
              ? student.courses
                  .split(", ")
                  .map((c) => `<span class="course-tag">${c}</span>`)
                  .join(" ")
              : '<span class="text-muted">No courses</span>'
          }</div>
          <small class="text-muted">
            Last activity: ${new Date(
              student.activity_date
            ).toLocaleDateString()}
          </small>
        </div>
      `
        )
        .join("");
    })
    .catch((err) => {
      console.error("Error fetching recent students:", err);
      container.innerHTML =
        '<div class="text-danger p-2">Network error. Try again.</div>';
    });
}

// =====================
// Student Actions
// =====================
function viewStudent(id) {
  window.location.href = `/view_student/${id}`;
}

function editStudent(id) {
  window.location.href = `/edit_student/${id}`;
}

function deleteStudent(id) {
  if (!confirm("Are you sure you want to delete this student?")) return;

  fetch(`/api/delete_student/${id}`, { method: "DELETE" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showNotification("Student deleted successfully!", "success");
        setTimeout(() => location.reload(), 1000);
      } else {
        showNotification(data.message || "Delete failed.", "error");
      }
    })
    .catch((err) => {
      console.error("Delete error:", err);
      showNotification("Network error while deleting.", "error");
    });
}

// =====================
// Form Validation
// =====================

// Main form validation function
function validateForm() {
  let isValid = true;

  // Validate all fields
  if (!validateStudentId()) isValid = false;
  if (!validateName()) isValid = false;
  if (!validateAge()) isValid = false;
  if (!validateEmail()) isValid = false;
  if (!validateCourses()) isValid = false;

  if (!isValid) {
    showNotification("Please fix the errors in the form before submitting.", "error");
    return false;
  }

  // Disable submit button to prevent double submission
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Adding...';
  }

  return true;
}

// Validate Student ID (must be positive integer)
function validateStudentId() {
  const studentIdInput = document.getElementById('student_id');
  const feedback = document.getElementById('student_id_feedback');
  const value = studentIdInput.value.trim();

  feedback.textContent = '';
  studentIdInput.classList.remove('is-invalid', 'is-valid');

  if (!value) {
    feedback.textContent = 'Student ID is required!';
    studentIdInput.classList.add('is-invalid');
    return false;
  }

  // Check if it's a valid positive integer
  const numValue = parseInt(value, 10);
  if (isNaN(numValue) || numValue <= 0) {
    feedback.textContent = 'Student ID must be a positive integer!';
    studentIdInput.classList.add('is-invalid');
    return false;
  }

  // Check if it's within reasonable range (1-9000000000)
  if (numValue >= 9000000000) {
    feedback.textContent = 'Student ID must be less than 9,000,000,000!';
    studentIdInput.classList.add('is-invalid');
    return false;
  }

  feedback.textContent = 'Valid student ID';
  studentIdInput.classList.add('is-valid');
  return true;
}

// Validate Name
function validateName() {
  const nameInput = document.getElementById('name');
  const feedback = document.getElementById('name_feedback');
  const value = nameInput.value.trim();

  feedback.textContent = '';
  nameInput.classList.remove('is-invalid', 'is-valid');

  if (!value) {
    feedback.textContent = 'Name is required!';
    nameInput.classList.add('is-invalid');
    return false;
  }

  if (value.length < 2) {
    feedback.textContent = 'Name must be at least 2 characters long!';
    nameInput.classList.add('is-invalid');
    return false;
  }

  if (value.length > 100) {
    feedback.textContent = 'Name must be less than 100 characters!';
    nameInput.classList.add('is-invalid');
    return false;
  }

  // Check for valid name characters (letters, spaces, hyphens, apostrophes)
  const nameRegex = /^[a-zA-Z\s\-']+$/;
  if (!nameRegex.test(value)) {
    feedback.textContent = 'Name can only contain letters, spaces, hyphens, and apostrophes!';
    nameInput.classList.add('is-invalid');
    return false;
  }

  feedback.textContent = 'Valid name';
  nameInput.classList.add('is-valid');
  return true;
}

// Validate Age
function validateAge() {
  const ageInput = document.getElementById('age');
  const feedback = document.getElementById('age_feedback');
  const value = ageInput.value.trim();

  feedback.textContent = '';
  ageInput.classList.remove('is-invalid', 'is-valid');

  if (!value) {
    feedback.textContent = 'Age is required!';
    ageInput.classList.add('is-invalid');
    return false;
  }

  const numValue = parseInt(value, 10);
  if (isNaN(numValue) || numValue <= 0) {
    feedback.textContent = 'Age must be a positive integer!';
    ageInput.classList.add('is-invalid');
    return false;
  }

  if (numValue > 150) {
    feedback.textContent = 'Age must be realistic (less than 150)!';
    ageInput.classList.add('is-invalid');
    return false;
  }

  feedback.textContent = 'Valid age';
  ageInput.classList.add('is-valid');
  return true;
}

// Validate Email
function validateEmail() {
  const emailInput = document.getElementById('email');
  const feedback = document.getElementById('email_feedback');
  const value = emailInput.value.trim();

  feedback.textContent = '';
  emailInput.classList.remove('is-invalid', 'is-valid');

  if (!value) {
    feedback.textContent = 'Email is required!';
    emailInput.classList.add('is-invalid');
    return false;
  }

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    feedback.textContent = 'Please enter a valid email address!';
    emailInput.classList.add('is-invalid');
    return false;
  }

  if (value.length > 255) {
    feedback.textContent = 'Email must be less than 255 characters!';
    emailInput.classList.add('is-invalid');
    return false;
  }

  feedback.textContent = 'Valid email';
  emailInput.classList.add('is-valid');
  return true;
}

// Validate Courses
function validateCourses() {
  const coursesInput = document.getElementById('courses');
  const feedback = document.getElementById('courses_feedback');
  const value = coursesInput.value.trim();

  feedback.textContent = '';
  coursesInput.classList.remove('is-invalid', 'is-valid');

  // Courses are optional, so empty is valid
  if (!value) {
    feedback.textContent = 'Optional field';
    coursesInput.classList.add('is-valid');
    return true;
  }

  // Split by comma and clean up
  const courses = value.split(',').map(course => course.trim()).filter(course => course.length > 0);

  if (courses.length > 10) {
    feedback.textContent = 'Maximum 10 courses allowed!';
    coursesInput.classList.add('is-invalid');
    return false;
  }

  // Check individual course names
  for (let i = 0; i < courses.length; i++) {
    if (courses[i].length > 100) {
      feedback.textContent = `Course "${courses[i]}" is too long (max 100 characters)!`;
      coursesInput.classList.add('is-invalid');
      return false;
    }

    // Check for valid course name characters
    const courseRegex = /^[a-zA-Z0-9\s\-&'()]+$/;
    if (!courseRegex.test(courses[i])) {
      feedback.textContent = `Course "${courses[i]}" contains invalid characters!`;
      coursesInput.classList.add('is-invalid');
      return false;
    }
  }

  feedback.textContent = `${courses.length} course(s) valid`;
  coursesInput.classList.add('is-valid');
  return true;
}

// =====================
// Form Submission
// =====================
function setupFormSubmission() {
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const data = {};
      formData.forEach((value, key) => (data[key] = value));

      fetch("/api/add_student", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then((res) => res.json())
        .then((resp) => {
          if (resp.success) {
            showNotification("Student added successfully!", "success");
            this.reset();
            setTimeout(() => (window.location.href = "index.html"), 1000);
          } else {
            showNotification(resp.message || "Failed to add student", "error");
          }
        })
        .catch((err) => {
          console.error("Add student error:", err);
          showNotification("Network error. Try again.", "error");
        });
    });
  });
}

// =====================
// Duplicate Checks
// =====================
function checkDuplicateStudentId(studentId, excludeId = null) {
  if (!studentId.trim()) return;

  fetch(
    `/api/check_duplicate?type=student_id&value=${encodeURIComponent(
      studentId
    )}&exclude_id=${excludeId || ""}`
  )
    .then((res) => res.json())
    .then((data) => {
      const feedback = document.getElementById("student_id_feedback");
      const input = document.getElementById("student_id");
      feedback.textContent = "";
      input.classList.remove("is-invalid", "is-valid");

      if (data.is_duplicate) {
        feedback.textContent = "Student ID already exists!";
        input.classList.add("is-invalid");
        showNotification("Student ID already exists!", "error");
      } else {
        feedback.textContent = "Student ID is available";
        input.classList.add("is-valid");
      }
    })
    .catch((err) => console.error("Duplicate check error:", err));
}

function checkDuplicateEmail(email, excludeId = null) {
  if (!email.trim()) return;

  fetch(
    `/api/check_duplicate?type=email&value=${encodeURIComponent(
      email
    )}&exclude_id=${excludeId || ""}`
  )
    .then((res) => res.json())
    .then((data) => {
      const feedback = document.getElementById("email_feedback");
      const input = document.getElementById("email");
      feedback.textContent = "";
      input.classList.remove("is-invalid", "is-valid");

      if (data.is_duplicate) {
        feedback.textContent = "Email already exists!";
        input.classList.add("is-invalid");
        showNotification("Email already exists!", "error");
      } else {
        feedback.textContent = "Email is available";
        input.classList.add("is-valid");
      }
    })
    .catch((err) => console.error("Duplicate check error:", err));
}

// =====================
// Live Search
// =====================
function performTableSearch(query) {
  fetch(`/api/search?q=${encodeURIComponent(query)}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        showNotification("Search error. Try again.", "error");
        return;
      }
      displayTableResults(data.results || [], query);
    })
    .catch((err) => {
      console.error("Search error:", err);
      showNotification("Network error during search.", "error");
    });
}

// =====================
// Display Results in Table
// =====================
function displayTableResults(results, query) {
  const section = document.getElementById("search-results-section");
  const tbody = document.getElementById("results-table-body");
  const count = document.getElementById("results-count");

  tbody.innerHTML = "";
  if (!results.length) {
    section.style.display = "none";
    showNotification("No students found.", "error");
    return;
  }

  section.style.display = "block";
  count.textContent = results.length;

  results.forEach((s) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${s.student_id || "N/A"}</td>
      <td>${s.name || "N/A"}</td>
      <td>${s.age || "N/A"}</td>
      <td>${s.email || "N/A"}</td>
      <td>${
        s.courses && s.courses !== "No courses"
          ? s.courses
              .split(", ")
              .map(
                (c) => `<span class="badge bg-light text-dark me-1">${c}</span>`
              )
              .join("")
          : '<span class="text-muted">No courses</span>'
      }</td>
      <td>
        <button class="btn btn-sm btn-outline-primary me-1" onclick="viewStudent(${s.id})"><i class="fas fa-eye"></i></button>
        <button class="btn btn-sm btn-outline-info me-1" onclick="editStudent(${s.id})"><i class="fas fa-edit"></i></button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${s.id})"><i class="fas fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(row);
  });

  showNotification(`Found ${results.length} student(s) for "${query}"`, "success");
}

// =====================
// Search Setup Functions
// =====================
function setupSearch() {
  // Search functionality is now handled directly in the search.html file
  // This function is kept for compatibility with other pages
}

function setupTableResults() {
  // Table results functionality is now handled directly in the search.html file
  // This function is kept for compatibility with other pages
}

function setupDeleteButtons() {
  // Delete button functionality is handled by the deleteStudent function
  // This function is kept for compatibility with other pages
}

function setupNotification() {
  // Notification functionality is handled by the showNotification function
  // This function is kept for compatibility with other pages
}
