document.addEventListener('DOMContentLoaded', () => {
    // Theme buttons
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            if (theme === 'dark') {
                document.body.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
            }
            showToast(`Theme changed to ${theme}`);
        });
    });
});

async function backupData() {
    showLoading();
    
    try {
        const response = await fetch('/api/backup', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Backup created successfully: ${data.filename}`);
        } else {
            showToast('Error creating backup', 'error');
        }
    } catch (error) {
        console.error('Error creating backup:', error);
        showToast('Error creating backup', 'error');
    } finally {
        hideLoading();
    }
}

async function restoreData() {
    if (!confirm('This will restore all data from the latest backup. Continue?')) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/restore', {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('Data restored successfully');
        } else {
            showToast('Error restoring data', 'error');
        }
    } catch (error) {
        console.error('Error restoring data:', error);
        showToast('Error restoring data', 'error');
    } finally {
        hideLoading();
    }
}

async function emptyTrash() {
    if (!confirm('Are you sure you want to permanently delete all files in trash?')) return;
    
    try {
        const response = await fetch('/api/trash', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Trash emptied successfully');
        } else {
            showToast('Error emptying trash', 'error');
        }
    } catch (error) {
        console.error('Error emptying trash:', error);
        showToast('Error emptying trash', 'error');
    }
}

function openIDsPage() {
    window.location.href = 'ids.html';
}