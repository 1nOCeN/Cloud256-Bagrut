    <?php
    // Database connection: host, username, password, database name
    $conn = new mysqli('localhost', 'cloud', 'rootme1', 'cloud');

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Check if form is submitted
    if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['submit'])) {

        // Collect form data
        $email = htmlspecialchars($_POST['Email']);
        $username = htmlspecialchars($_POST['Username']);
        $password = htmlspecialchars($_POST['Password']);

        // Hash the password for security
        $hashedPassword = password_hash($password, PASSWORD_BCRYPT);

        // Create SQL query (use correct variable for username)
        $add = "INSERT INTO users (email, password, username) VALUES ('$email', '$hashedPassword', '$username')";

        // Execute query and check if it was successful
        if ($conn->query($add) === TRUE) {
            // Redirect back to main program
            header("Location: Mainprogram.html");
            exit(); // Stop script execution after redirect
        } else {
            // Output error if query fails
            echo "Error: " . $conn->error;
        }

        // Close the database connection
        $conn->close();
    }
    ?>
