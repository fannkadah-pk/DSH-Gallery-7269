document.addEventListener('DOMContentLoaded', () => {
    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        // For demo, check if username is 'admin' and password is 'securepassword123'
        if (username === 'admin' && password === 'securepassword123') {
            // Show welcome message
            const welcome = document.getElementById('welcomeMessage');
            welcome.style.display = 'block';

            setTimeout(() => {
                localStorage.setItem('showWelcome', 'true');
                // Redirect to home
                window.location.href = 'index.html';
            }, 3000);
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        alert('Login failed');
    }
}