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