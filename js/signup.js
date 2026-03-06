document.addEventListener('DOMContentLoaded', () => {
    // Signup form submission
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

async function handleSignup(e) {
    e.preventDefault();

    const formData = {
        fullName: document.getElementById('fullName').value,
        username: document.getElementById('username').value,
        countryCode: document.getElementById('countryCode').value,
        contact: document.getElementById('contact').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };

    try {
        const response = await fetch('/api/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            // Show welcome message
            const welcome = document.getElementById('welcomeMessage');
            welcome.style.display = 'block';

            setTimeout(() => {
                window.location.href = 'login.html';
            }, 3000);
        } else {
            alert(result.error || 'Signup failed');
        }
    } catch (error) {
        alert('Signup failed. Please try again.');
    }
}