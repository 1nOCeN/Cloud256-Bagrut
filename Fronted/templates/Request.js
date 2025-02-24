 // Connect to the SocketIO server
    const socket = io.connect("http://localhost:5000");

    // Listen for incoming file access requests
    socket.on("file_request", function(data) {
        // When a request is received, show the modal and populate it with details
        document.getElementById("requestDetails").innerHTML = `User ${data.from} has requested access to the file: ${data.filename}`;
        document.getElementById("requestModal").style.display = "block"; // Show the modal
    });

    // Close the modal
    function closeModal() {
        document.getElementById("requestModal").style.display = "none";
    }

    // Approve the request
    function approveRequest() {
        // Send the approval to the server
        socket.emit('approve_request', { status: 'approved' });
        closeModal(); // Close the modal
    }

    // Deny the request
    function denyRequest() {
        // Send the denial to the server
        socket.emit('approve_request', { status: 'denied' });
        closeModal(); // Close the modal
    }
