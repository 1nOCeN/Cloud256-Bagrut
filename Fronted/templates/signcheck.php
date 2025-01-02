<?php
// Database connection
$conn = new mysqli('localhost', 'cloud', 'rootme1', 'cloud');

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Check if form was submitted
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['Login'])) {
    // Collect login data
    $email = htmlspecialchars($_POST['Email']);
    $password = htmlspecialchars($_POST['Password']);

    // Query to find the user by email
    $query = "SELECT * FROM users WHERE Email = ?";
    $stmt = $conn->prepare($query);
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        // User found, fetch their data
        $user = $result->fetch_assoc();

        // Verify the password using password_verify()
        if (password_verify($password, $user['password'])) {
            // Login successful
            session_start();
            $_SESSION['user_id'] = $user['id']; // Save user ID to session
            $_SESSION['username'] = $user['username']; // Save username to session

            // Redirect to the main program/dashboard
            header("Location: Mainprogram.html");
            exit();
        } else {
            // Incorrect password
            echo "<p>Invalid password. Please try again.</p>";
        }
    } else {
        // Email not found
        echo "<p>No user found with this email. Please sign up.</p>";
    }

    // Close the prepared statement and connection
    $stmt->close();
    $conn->close();
}
?>
