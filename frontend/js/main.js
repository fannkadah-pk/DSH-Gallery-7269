// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme === 'dark' ? 'dark-theme' : '';
    
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        themeToggle.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        themeToggle.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// WhatsApp Integration
function openWhatsApp(type) {
    const phoneNumber = '+923306596115';
    let message = '';
    
    switch(type) {
        case 'help':
            message = 'Get Help for PCW Gallery';
            break;
        case 'error':
            message = 'Error and Problem';
            break;
        case 'backup':
            message = 'How to get Backup my Data';
            break;
        default:
            message = 'Help for PCW Gallery';
    }
    
    const url = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// File Size Formatter
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    
    // Theme toggle event listener
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Load counts for home page
    if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
        loadFileCounts();
    }
});

// Load file counts for home page
async function loadFileCounts() {
    try {
        const response = await fetch('/api/counts');
        const counts = await response.json();
        
        document.getElementById('imageCount').textContent = counts.images || 0;
        document.getElementById('videoCount').textContent = counts.videos || 0;
        document.getElementById('audioCount').textContent = counts.audio || 0;
        document.getElementById('documentCount').textContent = counts.documents || 0;
    } catch (error) {
        console.error('Error loading counts:', error);
    }
}