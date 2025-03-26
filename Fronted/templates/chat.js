// Establish Socket.IO connection with error handling
const socket = io.connect();
const room = "{{ room }}";
const currentUser = "{{ session['username'] }}";

// DOM elements
const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const typingIndicator = document.getElementById('typing-indicator');

// Connection status handling
socket.on('connect', () => {
    console.log("Connected to Socket.IO server");
    showConnectionStatus('connected');
    
    // Join the chat room
    socket.emit('join', {
        username: currentUser,
        room: room
    });
});

socket.on('disconnect', () => {
    console.log("Disconnected from Socket.IO server");
    showConnectionStatus('disconnected');
});

socket.on('connect_error', (error) => {
    console.error("Connection error:", error);
    showConnectionStatus('error');
});

// Message handling
socket.on('receive_message', function(data) {
    appendMessage(data.username, data.message, data.timestamp || new Date().toISOString(), 
                 data.username === currentUser ? 'outgoing' : 'incoming');
});

// User activity handling
socket.on('user_joined', function(data) {
    appendSystemMessage(`${data.username} has joined the chat`);
});

socket.on('user_left', function(data) {
    appendSystemMessage(`${data.username} has left the chat`);
});

socket.on('typing', function(data) {
    if (data.username !== currentUser) {
        showTypingIndicator(data.username, data.isTyping);
    }
});

// Send a message
function sendMessage() {
    const message = messageInput.value.trim();
    if (message !== "") {
        const timestamp = new Date().toISOString();
        
        socket.emit('message', {
            room: room,
            message: message,
            username: currentUser,
            timestamp: timestamp
        });
        
        // Optimistically render our own message immediately
        appendMessage(currentUser, message, timestamp, 'outgoing');
        
        // Clear the input field and reset typing status
        messageInput.value = '';
        socket.emit('typing', {
            room: room,
            username: currentUser,
            isTyping: false
        });
    }
}

// Show typing indicator when user is typing
let typingTimeout;
messageInput.addEventListener('input', function() {
    socket.emit('typing', {
        room: room,
        username: currentUser,
        isTyping: messageInput.value.trim() !== ''
    });
    
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit('typing', {
            room: room,
            username: currentUser,
            isTyping: false
        });
    }, 2000); // Stop "typing" after 2 seconds of inactivity
});

// Event listeners
messageInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent default to avoid newline
        sendMessage();
    }
});

sendButton.addEventListener('click', sendMessage);

// Helper functions
function appendMessage(username, message, timestamp, type) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    
    const formattedTime = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="username">${username}</span>
            <span class="timestamp">${formattedTime}</span>
        </div>
        <div class="message-body">${formatMessage(message)}</div>
    `;
    
    chatBox.appendChild(messageElement);
    scrollToBottom();
}

function appendSystemMessage(text) {
    const systemMessage = document.createElement('div');
    systemMessage.className = 'system-message';
    systemMessage.textContent = text;
    
    chatBox.appendChild(systemMessage);
    scrollToBottom();
}

function showTypingIndicator(username, isTyping) {
    if (isTyping) {
        typingIndicator.textContent = `${username} is typing...`;
        typingIndicator.style.display = 'block';
    } else {
        typingIndicator.style.display = 'none';
    }
}

function showConnectionStatus(status) {
    const statusBar = document.getElementById('connection-status');
    statusBar.className = `status-bar ${status}`;
    
    switch (status) {
        case 'connected':
            statusBar.textContent = 'Connected';
            break;
        case 'disconnected':
            statusBar.textContent = 'Disconnected. Trying to reconnect...';
            break;
        case 'error':
            statusBar.textContent = 'Connection error. Please refresh the page.';
            break;
    }
}

function formatMessage(message) {
    // Convert URLs to clickable links
    return message.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    )
    // Convert line breaks to <br>
    .replace(/\n/g, '<br>');
}

function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Initial connection status
showConnectionStatus('connecting');