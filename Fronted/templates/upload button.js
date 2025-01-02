function saveFiles() {
    const fileInput = document.getElementById("fileInput");
    const files = fileInput.files;
    const savedFiles = JSON.parse(localStorage.getItem("myFiles")) || [];

    if (files.length === 0) {
        alert("No files selected!");
        return;
    }

    for (const file of files) {
        const reader = new FileReader();

        reader.onload = function (event) {
            const fileData = {
                name: file.name,
                size: file.size,
                type: file.type,
                content: event.target.result,
            };

            savedFiles.push(fileData);
            localStorage.setItem("myFiles", JSON.stringify(savedFiles)); // Save files in localStorage
            displayFiles();
        };

        reader.readAsDataURL(file); // Convert file to Base64 format
    }
}

// Display the saved files
function displayFiles() {
    const fileList = document.getElementById("fileList");
    const savedFiles = JSON.parse(localStorage.getItem("myFiles")) || [];

    fileList.innerHTML = "";

    savedFiles.forEach((file, index) => {
        const fileItem = document.createElement("div");
        fileItem.className = "file-item";
        fileItem.innerHTML = `
            <strong>${file.name}</strong> (${(file.size / 1024).toFixed(2)} KB)
            <br>
            <a href="${file.content}" download="${file.name}">Download</a>
        `;
        fileList.appendChild(fileItem);
    });
}

// Display files on page load
document.addEventListener("DOMContentLoaded", displayFiles);

function toggleBox() {
    const box = document.getElementById('box2');
    box.classList.toggle('visible');
}
setTimeout(() => {
    const textElement = document.getElementById("animated-text");
    const formElement = document.getElementById("login-form");

    // Hide the animated text
    textElement.style.display = "none";

    // Show the login form
    formElement.style.display = "flex";
  }, 3000); // 3 seconds (match the animation duration)