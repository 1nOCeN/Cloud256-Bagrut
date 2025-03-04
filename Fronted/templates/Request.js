const socket = io();

socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('file_request', function(data) {
    console.log('Received file request:', data);
    
    // Update modal content
    const requestDetails = document.getElementById('requestDetails');
    requestDetails.textContent = `User ${data.from} has requested access to file: ${data.filename}`;

    // Store request data for later use
    requestDetails.dataset.requestId = data.requestId; 

    // Show the modal
    document.getElementById('requestModal').style.display = 'block';
});

// Function to close the modal
function closeModal() {
    document.getElementById('requestModal').style.display = 'none';
}

// Function to handle request approval
function approveRequest() {
    const requestId = document.getElementById('requestDetails').dataset.requestId;
    socket.emit('approve_request', { requestId });

    alert('Request approved.');
    closeModal();
}

// Function to handle request denial
function denyRequest() {
    const requestId = document.getElementById('requestDetails').dataset.requestId;
    socket.emit('deny_request', { requestId });

    alert('Request denied.');
    closeModal();
}
