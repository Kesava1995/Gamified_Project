// --- STATE ---
let teacherData = null;
let currentQuizId = null;
let analyticsChart = null; // To hold the chart instance

// --- DOM ELEMENTS ---
const rosterManagementDiv = document.getElementById('roster-management');
const unassignedStudentSelect = document.getElementById('unassigned-student-select');
const enrollStudentBtn = document.getElementById('enroll-student-btn');
const loginPage = document.getElementById('teacher-login-page');
const dashboardPage = document.getElementById('dashboard-page');
const loginBtn = document.getElementById('teacher-login-btn');
const classSelect = document.getElementById('class-select');
const chartCanvas = document.getElementById('analytics-chart');
const createQuizBtn = document.getElementById('create-quiz-btn');
const quizListDiv = document.getElementById('quiz-list');
const addQuestionModal = document.getElementById('add-question-modal');

// --- EVENT LISTENERS ---
enrollStudentBtn.addEventListener('click', handleEnrollStudent);
loginBtn.addEventListener('click', handleTeacherLogin);
classSelect.addEventListener('change', handleClassSelection);
document.getElementById('logout-btn').addEventListener('click', () => {
    dashboardPage.classList.add('hidden');
    loginPage.classList.remove('hidden');
    document.getElementById('teacher-username').value = '';
    document.getElementById('teacher-password').value = '';
});
createQuizBtn.addEventListener('click', handleCreateQuiz);
addQuestionModal.querySelector('.close-btn').onclick = () => addQuestionModal.classList.add('hidden');
addQuestionModal.querySelector('#save-question-btn').onclick = handleSaveQuestion;

// --- LOGIN LOGIC ---
async function handleTeacherLogin() {
    const username = document.getElementById('teacher-username').value;
    const password = document.getElementById('teacher-password').value;
    if (!username || !password) return alert('Please enter username and password.');

    const response = await fetch('/api/teacher/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const result = await response.json();

    if (result.success) {
        loginPage.classList.add('hidden');
        dashboardPage.classList.remove('hidden');
        document.getElementById('dashboard-title').textContent = `Welcome, ${result.username}`;
        
        teacherData = result; // Save teacher data
        populateClassDropdown(result.classes);
        loadTeacherQuizzes(); // Fetch quizzes on login
    } else {
        alert(`Login failed: ${result.message}`);
    }
}

// --- DASHBOARD LOGIC ---
function populateClassDropdown(classes) {
    classSelect.innerHTML = '<option value="">-- Select a Class --</option>';
    classes.forEach(cls => {
        const option = document.createElement('option');
        option.value = cls.id;
        option.textContent = cls.class_name;
        classSelect.appendChild(option);
    });
}

async function handleClassSelection() {
    const classId = classSelect.value;
    if (classId) {
        rosterManagementDiv.classList.remove('hidden');
        loadUnassignedStudents(classId); // Load students for the selected class
    } else {
        rosterManagementDiv.classList.add('hidden');
    }
    if (!classId) {
        if (analyticsChart) analyticsChart.destroy();
        return;
    }
    const response = await fetch(`/api/teacher/analytics/${classId}`);
    if (!response.ok) {
        alert('Could not fetch analytics for this class.');
        return;
    }
    const data = await response.json();
    renderChart(data);
}

async function loadUnassignedStudents(classId) {
    const response = await fetch(`/api/teacher/unassigned_students/${classId}`);
    const students = await response.json();

    unassignedStudentSelect.innerHTML = '<option value="">-- Select a student to add --</option>';
    if (students.length === 0) {
        unassignedStudentSelect.innerHTML = '<option value="">-- All students enrolled --</option>';
    }
    
    students.forEach(student => {
        const option = document.createElement('option');
        option.value = student.id;
        option.textContent = student.username;
        unassignedStudentSelect.appendChild(option);
    });
}

async function handleEnrollStudent() {
    const classId = classSelect.value;
    const userId = unassignedStudentSelect.value;

    if (!classId || !userId) {
        return alert('Please select both a class and a student.');
    }

    const response = await fetch('/api/teacher/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, class_id: classId })
    });

    const result = await response.json();
    if (result.success) {
        alert('Student enrolled successfully!');
        // Refresh the student list and the analytics
        handleClassSelection();
    } else {
        alert(`Error: ${result.message}`);
    }
}

function renderChart(data) {
    if (analyticsChart) analyticsChart.destroy();
    analyticsChart = new Chart(chartCanvas, {
        type: 'bar',
        data: data,
        options: {
            scales: { y: { beginAtZero: true, title: { display: true, text: 'Average Score' } } },
            responsive: true,
            plugins: { legend: { position: 'top' }, title: { display: true, text: 'Class Performance by Subject' } }
        }
    });
}

// --- QUIZ MANAGEMENT LOGIC ---
async function loadTeacherQuizzes() {
    const response = await fetch(`/api/teacher/quizzes?teacher_id=${teacherData.teacher_id}`);
    const quizzes = await response.json();
    quizListDiv.innerHTML = '';
    quizzes.forEach(quiz => {
        const quizEl = document.createElement('div');
        quizEl.className = 'quiz-item';
        quizEl.innerHTML = `
            <span>${quiz.name}</span>
            <div>
                <button class="small-btn add-q" data-quiz-id="${quiz.id}" data-quiz-name="${quiz.name}">Add Question</button>
                <button class="small-btn assign-q" data-quiz-id="${quiz.id}">Assign</button>
            </div>
        `;
        quizListDiv.appendChild(quizEl);
    });
    document.querySelectorAll('.add-q').forEach(btn => btn.onclick = openAddQuestionModal);
    document.querySelectorAll('.assign-q').forEach(btn => btn.onclick = handleAssignQuiz);
}

async function handleCreateQuiz() {
    const name = document.getElementById('new-quiz-name').value;
    if (!name) return alert('Please enter a quiz name.');
    
    const response = await fetch('/api/teacher/quizzes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, teacher_id: teacherData.teacher_id })
    });
    if (response.ok) {
        document.getElementById('new-quiz-name').value = '';
        loadTeacherQuizzes();
    }
}

function openAddQuestionModal(event) {
    currentQuizId = event.target.dataset.quizId;
    addQuestionModal.querySelector('#modal-quiz-name').textContent = `Add Question to: ${event.target.dataset.quizName}`;
    addQuestionModal.classList.remove('hidden');
}

async function handleSaveQuestion() {
    const question_text = document.getElementById('question-text').value;
    const options = [
        document.getElementById('option1').value,
        document.getElementById('option2').value,
        document.getElementById('option3').value
    ];
    const correctIndex = document.getElementById('correct-answer-select').value;
    const correct_answer = options[correctIndex - 1];

    if (!question_text || options.some(opt => !opt)) return alert('Please fill all fields.');

    await fetch('/api/teacher/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: currentQuizId, question_text, options, correct_answer })
    });

    // Clear fields and hide modal
    ['question-text', 'option1', 'option2', 'option3'].forEach(id => document.getElementById(id).value = '');
    addQuestionModal.classList.add('hidden');
}

async function handleAssignQuiz(event) {
    const quizId = event.target.dataset.quizId;
    const classId = classSelect.value;
    if (!classId) return alert('Please select a class from the analytics dropdown first.');
    
    await fetch('/api/teacher/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: quizId, class_id: classId })
    });
    alert('Quiz assigned successfully!');
}