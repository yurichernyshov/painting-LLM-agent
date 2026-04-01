// Socket.IO connection
const socket = io();

// Canvas setup
const canvas = document.getElementById('shapesCanvas');
const ctx = canvas.getContext('2d');
const shapeCountElement = document.getElementById('shapeCount');

// Auth elements
const authSection = document.getElementById('authSection');
const mainContent = document.getElementById('mainContent');
const usernameDisplay = document.getElementById('usernameDisplay');

// Chat elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// Panels
const statsPanel = document.getElementById('statsPanel');
const statsContent = document.getElementById('statsContent');
const suggestionsPanel = document.getElementById('suggestionsPanel');
const suggestionsContent = document.getElementById('suggestionsContent');

// Current state
let currentShapes = [];
let currentUser = null;
let authToken = null;

// Socket event listeners
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    logout();
});

socket.on('auth_response', (response) => {
    if (response.success) {
        currentUser = {
            id: response.user_id,
            username: response.username
        };
        authToken = response.token;
        
        // Show main content
        authSection.style.display = 'none';
        mainContent.style.display = 'block';
        usernameDisplay.textContent = response.username;
        
        // Enable inputs
        messageInput.disabled = false;
        sendButton.disabled = false;
        document.querySelectorAll('.quick-commands button').forEach(btn => {
            btn.disabled = false;
        });
        
        addMessage(response.message, 'agent', 'success');
    } else {
        addMessage(response.message, 'agent', 'error');
    }
});

socket.on('initial_shapes', (shapes) => {
    currentShapes = shapes;
    drawShapes();
    updateShapeCount();
});

socket.on('shapes_updated', (shapes) => {
    currentShapes = shapes;
    drawShapes();
    updateShapeCount();
});

socket.on('agent_response', (response) => {
    const messageClass = response.success ? 'success' : (response.action === 'help' ? 'info' : 'error');
    addMessage(response.message, 'agent', messageClass);
});

socket.on('stats_updated', (stats) => {
    if (stats.error) {
        statsContent.innerHTML = `<p class="error">${stats.error}</p>`;
    } else {
        let html = `<div class="stat-item"><strong>Total Shapes Drawn:</strong> ${stats.total_shapes}</div>`;
        
        if (stats.favorites && stats.favorites.length > 0) {
            html += `<div class="stat-item"><strong>Favorite Shapes:</strong><br>`;
            stats.favorites.forEach(fav => {
                html += `&nbsp;&nbsp;• ${fav.count} ${fav.color} ${fav.shape_type}(s)<br>`;
            });
            html += `</div>`;
        }
        
        if (stats.all_shapes && stats.all_shapes.length > 0) {
            html += `<div class="stat-item"><strong>All Shapes:</strong><br>`;
            stats.all_shapes.forEach(shape => {
                html += `&nbsp;&nbsp;• ${shape.count} ${shape.color} ${shape.shape_type}(s)<br>`;
            });
            html += `</div>`;
        }
        
        statsContent.innerHTML = html;
    }
    statsPanel.style.display = 'block';
});

socket.on('suggestions_updated', (data) => {
    if (data.error) {
        suggestionsContent.innerHTML = `<p class="error">${data.error}</p>`;
    } else {
        suggestionsContent.innerHTML = `<p>${data.suggestions}</p>`;
    }
    suggestionsPanel.style.display = 'block';
});

// Auth functions
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    
    if (tab === 'login') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }
}

function register() {
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    if (!username || !password) {
        addMessage('Please fill in all fields', 'agent', 'error');
        return;
    }
    
    if (password !== passwordConfirm) {
        addMessage('Passwords do not match', 'agent', 'error');
        return;
    }
    
    socket.emit('register_user', { username, password });
}

function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        addMessage('Please fill in all fields', 'agent', 'error');
        return;
    }
    
    socket.emit('login_user', { username, password });
}

function logout() {
    currentUser = null;
    authToken = null;
    currentShapes = [];
    
    // Show auth section
    authSection.style.display = 'block';
    mainContent.style.display = 'none';
    
    // Disable inputs
    messageInput.disabled = true;
    sendButton.disabled = true;
    document.querySelectorAll('.quick-commands button').forEach(btn => {
        btn.disabled = true;
    });
    
    // Clear forms
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('registerUsername').value = '';
    document.getElementById('registerPassword').value = '';
    document.getElementById('registerPasswordConfirm').value = '';
    
    addMessage('Logged out successfully', 'agent', 'info');
}

// Canvas functions
function drawShapes() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    currentShapes.forEach(shape => {
        ctx.fillStyle = shape.color;
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        
        switch(shape.shape_type) {
            case 'circle':
                drawCircle(shape.x, shape.y, shape.size);
                break;
            case 'rectangle':
                drawRectangle(shape.x, shape.y, shape.size);
                break;
            case 'triangle':
                drawTriangle(shape.x, shape.y, shape.size);
                break;
        }
    });
}

function drawCircle(x, y, radius) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
}

function drawRectangle(x, y, size) {
    const width = size * 1.5;
    const height = size;
    ctx.fillRect(x - width/2, y - height/2, width, height);
    ctx.strokeRect(x - width/2, y - height/2, width, height);
}

function drawTriangle(x, y, size) {
    const height = size * 1.2;
    const width = size * 1.5;
    
    ctx.beginPath();
    ctx.moveTo(x, y - height/2);
    ctx.lineTo(x - width/2, y + height/2);
    ctx.lineTo(x + width/2, y + height/2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
}

function updateShapeCount() {
    shapeCountElement.textContent = currentShapes.length;
}

// Chat functions
function addMessage(text, sender, extraClass = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender} ${extraClass}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addUserMessage(text) {
    addMessage(text, 'user');
}

function sendCommand(command) {
    if (!command.trim() || !currentUser) return;
    
    addUserMessage(command);
    socket.emit('chat_message', { message: command });
    messageInput.value = '';
}

function getStats() {
    socket.emit('get_stats');
}

function closeStats() {
    statsPanel.style.display = 'none';
}

function getSuggestions() {
    socket.emit('get_suggestions');
}

function closeSuggestions() {
    suggestionsPanel.style.display = 'none';
}

// Event listeners
sendButton.addEventListener('click', () => {
    sendCommand(messageInput.value);
});

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendCommand(messageInput.value);
    }
});

// Initialize
drawShapes();
updateShapeCount();
