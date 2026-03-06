document.addEventListener('DOMContentLoaded', () => {
    loadTrash();
    setupTrashEventListeners();
});

function setupTrashEventListeners() {
    // Search input
    document.getElementById('searchInput').addEventListener('input', (e) => {
        searchTrash(e.target.value);
    });
}

let allTrashImages = [];
let allTrashVideos = [];
let allTrashAudio = [];
let allTrashDocuments = [];
let currentTrashSearch = '';

document.addEventListener('DOMContentLoaded', () => {
    loadTrash();
    setupTrashEventListeners();
});

async function loadTrash() {
    showLoading();
    
    try {
        const response = await fetch('/api/trash');
        const trash = await response.json();
        
        allTrashImages = trash.images || [];
        allTrashVideos = trash.videos || [];
        allTrashAudio = trash.audio || [];
        allTrashDocuments = trash.documents || [];
        
        displayTrashItems('images', allTrashImages);
        displayTrashItems('videos', allTrashVideos);
        displayTrashItems('audio', allTrashAudio);
        displayTrashItems('documents', allTrashDocuments);
        
        hideLoading();
    } catch (error) {
        console.error('Error loading trash:', error);
        showToast('Error loading trash', 'error');
        hideLoading();
    }
}

function getFilteredTrash() {
    let images = allTrashImages;
    let videos = allTrashVideos;
    let audio = allTrashAudio;
    let documents = allTrashDocuments;
    
    if (currentTrashSearch) {
        const searchLower = currentTrashSearch.toLowerCase();
        images = images.filter(item => item.originalname.toLowerCase().includes(searchLower));
        videos = videos.filter(item => item.originalname.toLowerCase().includes(searchLower));
        audio = audio.filter(item => item.originalname.toLowerCase().includes(searchLower));
        documents = documents.filter(item => item.originalname.toLowerCase().includes(searchLower));
    }
    
    return { images, videos, audio, documents };
}

function searchTrash(searchTerm) {
    currentTrashSearch = searchTerm;
    const filtered = getFilteredTrash();
    displayTrashItems('images', filtered.images);
    displayTrashItems('videos', filtered.videos);
    displayTrashItems('audio', filtered.audio);
    displayTrashItems('documents', filtered.documents);
}

function displayTrashItems(type, items) {
    const grid = document.querySelector(`.${type}-trash`);
    if (!grid) return;
    
    if (items.length === 0) {
        grid.innerHTML = '<p class="no-items">No items in trash</p>';
        return;
    }
    
    grid.innerHTML = items.map(item => createTrashItem(item, type)).join('');
}

function createTrashItem(item, type) {
    const icon = getTrashItemIcon(type, item.mimetype);
    const iconClass = type === 'images' ? 'fa-image' : 
                      type === 'videos' ? 'fa-video' :
                      type === 'audio' ? 'fa-music' : 'fa-file';
    
    return `
        <div class="media-item" data-id="${item.id}">
            <div style="padding: 2rem; text-align: center; background: var(--secondary-color);">
                <i class="fas ${iconClass}" style="font-size: 3rem; color: var(--primary-color);"></i>
            </div>
            <div class="media-info">
                <div class="media-name">${item.originalname}</div>
                <div class="media-size">${formatFileSize(item.size)}</div>
                <div class="media-date">Deleted: ${new Date(item.deleted_at).toLocaleDateString()}</div>
            </div>
            <div class="media-actions">
                <div class="action-icon" onclick="restoreItem('${item.id}')" title="Restore">
                    <i class="fas fa-undo"></i>
                </div>
                <div class="action-icon" onclick="deletePermanently('${item.id}')" title="Delete Permanently">
                    <i class="fas fa-trash"></i>
                </div>
            </div>
        </div>
    `;
}

function getTrashItemIcon(type, mimetype) {
    if (type === 'images') return 'fa-image';
    if (type === 'videos') return 'fa-video';
    if (type === 'audio') return 'fa-music';
    
    if (mimetype.includes('pdf')) return 'fa-file-pdf';
    if (mimetype.includes('word')) return 'fa-file-word';
    if (mimetype.includes('excel')) return 'fa-file-excel';
    if (mimetype.includes('powerpoint')) return 'fa-file-powerpoint';
    return 'fa-file';
}

async function restoreItem(itemId) {
    try {
        const response = await fetch(`/api/trash/${itemId}/restore`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('Item restored successfully');
            loadTrash(); // Reload trash
        } else {
            showToast('Error restoring item', 'error');
        }
    } catch (error) {
        console.error('Error restoring item:', error);
        showToast('Error restoring item', 'error');
    }
}

async function deletePermanently(itemId) {
    if (!confirm('Are you sure you want to permanently delete this item?')) return;
    
    try {
        const response = await fetch(`/api/trash/${itemId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Item deleted permanently');
            loadTrash(); // Reload trash
        } else {
            showToast('Error deleting item', 'error');
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        showToast('Error deleting item', 'error');
    }
}

async function restoreAll() {
    if (!confirm('Restore all items from trash?')) return;
    
    try {
        const response = await fetch('/api/trash/restore-all', {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('All items restored');
            loadTrash(); // Reload trash
        } else {
            showToast('Error restoring items', 'error');
        }
    } catch (error) {
        console.error('Error restoring items:', error);
        showToast('Error restoring items', 'error');
    }
}

async function deleteAllPermanently() {
    if (!confirm('Are you sure you want to permanently delete all items in trash?')) return;
    
    try {
        const response = await fetch('/api/trash', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('All items deleted permanently');
            loadTrash(); // Reload trash
        } else {
            showToast('Error deleting items', 'error');
        }
    } catch (error) {
        console.error('Error deleting items:', error);
        showToast('Error deleting items', 'error');
    }
}

function showLoading() {
    const container = document.querySelector('.trash-sections');
    if (container) {
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        spinner.id = 'loadingSpinner';
        container.appendChild(spinner);
    }
}

function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}