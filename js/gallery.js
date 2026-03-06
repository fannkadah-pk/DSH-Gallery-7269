let currentFilter = 'all';
let allImages = [];
let allVideos = [];
let allAudio = [];
let allDocuments = [];
let currentSearch = '';

document.addEventListener('DOMContentLoaded', () => {
    loadGallery();
    setupEventListeners();
});

function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            filterGallery();
        });
    });

    // Search input
    document.getElementById('searchInput').addEventListener('input', (e) => {
        searchGallery(e.target.value);
    });

    // Upload form
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);
    
    // File input change
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
}

async function loadGallery() {
    showLoading();
    
    try {
        const response = await fetch('/api/files');
        const files = await response.json();
        
        allImages = files.images || [];
        allVideos = files.videos || [];
        allAudio = files.audio || [];
        allDocuments = files.documents || [];
        
        displayImages(allImages);
        displayVideos(allVideos);
        displayAudio(allAudio);
        displayDocuments(files.documents || []);
        
        hideLoading();
    } catch (error) {
        console.error('Error loading gallery:', error);
        showToast('Error loading files', 'error');
        hideLoading();
    }
}
function getFilteredData() {
    let images = allImages;
    let videos = allVideos;
    let audio = allAudio;
    let documents = allDocuments;
    
    // Apply search filter
    if (currentSearch) {
        const searchLower = currentSearch.toLowerCase();
        images = images.filter(item => item.originalname.toLowerCase().includes(searchLower));
        videos = videos.filter(item => item.originalname.toLowerCase().includes(searchLower));
        audio = audio.filter(item => item.originalname.toLowerCase().includes(searchLower));
        documents = documents.filter(item => item.originalname.toLowerCase().includes(searchLower));
    }
    
    // Apply type filter
    if (currentFilter !== 'all') {
        if (currentFilter === 'images') {
            videos = [];
            audio = [];
            documents = [];
        } else if (currentFilter === 'videos') {
            images = [];
            audio = [];
            documents = [];
        } else if (currentFilter === 'audio') {
            images = [];
            videos = [];
            documents = [];
        } else if (currentFilter === 'documents') {
            images = [];
            videos = [];
            audio = [];
        }
    }
    
    return { images, videos, audio, documents };
}

function filterGallery() {
    const filtered = getFilteredData();
    displayImages(filtered.images);
    displayVideos(filtered.videos);
    displayAudio(filtered.audio);
    displayDocuments(filtered.documents);
}

function searchGallery(searchTerm) {
    currentSearch = searchTerm;
    filterGallery();
}
function displayImages(images) {
    const grid = document.querySelector('.images-grid');
    if (!grid) return;
    
    grid.innerHTML = images.map(image => createImageCard(image)).join('');
}

function displayVideos(videos) {
    const grid = document.querySelector('.videos-grid');
    if (!grid) return;
    
    grid.innerHTML = videos.map(video => createVideoCard(video)).join('');
}

function displayAudio(audioFiles) {
    const grid = document.querySelector('.audio-grid');
    if (!grid) return;
    
    grid.innerHTML = audioFiles.map(audio => createAudioCard(audio)).join('');
}

function displayDocuments(documents) {
    const grid = document.querySelector('.documents-grid');
    if (!grid) return;
    
    grid.innerHTML = documents.map(doc => createDocumentCard(doc)).join('');
}

function createImageCard(image) {
    // support both uploaded files and static assets
    const src = image.filename.startsWith('assets/') ? image.filename : "/uploads/" + image.filename;
    const isAsset = String(image.id).startsWith('asset-');
    return `
        <div class="media-item" data-id="${image.id}">
            <img src="${src}" alt="${image.originalname}">
            <div class="media-info">
                <div class="media-name">${image.originalname}</div>
                <div class="media-size">${formatFileSize(image.size)}</div>
            </div>
            <div class="media-actions">
                ${isAsset ? '' : `
                <div class="action-icon" onclick="deleteFile('${image.id}', 'images')" title="Delete">
                    <i class="fas fa-trash"></i>
                </div>
                <div class="action-icon" onclick="downloadFile('${image.id}')" title="Download">
                    <i class="fas fa-download"></i>
                </div>`}
            </div>
        </div>
    `;
}

function createVideoCard(video) {
    return `
        <div class="media-item" data-id="${video.id}">
            <video src="/uploads/${video.filename}"></video>
            <div class="media-info">
                <div class="media-name">${video.originalname}</div>
                <div class="media-size">${formatFileSize(video.size)}</div>
            </div>
            <div class="media-actions">
                <div class="action-icon" onclick="deleteFile('${video.id}', 'videos')" title="Delete">
                    <i class="fas fa-trash"></i>
                </div>
                <div class="action-icon" onclick="downloadFile('${video.id}')" title="Download">
                    <i class="fas fa-download"></i>
                </div>
            </div>
        </div>
    `;
}

function createAudioCard(audio) {
    return `
        <div class="media-item" data-id="${audio.id}">
            <div style="padding: 2rem; text-align: center; background: var(--secondary-color);">
                <i class="fas fa-music" style="font-size: 3rem; color: var(--primary-color);"></i>
            </div>
            <div class="media-info">
                <div class="media-name">${audio.originalname}</div>
                <div class="media-size">${formatFileSize(audio.size)}</div>
            </div>
            <div class="media-actions">
                <div class="action-icon" onclick="deleteFile('${audio.id}', 'audio')" title="Delete">
                    <i class="fas fa-trash"></i>
                </div>
                <div class="action-icon" onclick="downloadFile('${audio.id}')" title="Download">
                    <i class="fas fa-download"></i>
                </div>
            </div>
        </div>
    `;
}

function createDocumentCard(doc) {
    const icon = getDocumentIcon(doc.mimetype);
    
    return `
        <div class="media-item" data-id="${doc.id}">
            <div style="padding: 2rem; text-align: center; background: var(--secondary-color);">
                <i class="fas ${icon}" style="font-size: 3rem; color: var(--primary-color);"></i>
            </div>
            <div class="media-info">
                <div class="media-name">${doc.originalname}</div>
                <div class="media-size">${formatFileSize(doc.size)}</div>
            </div>
            <div class="media-actions">
                <div class="action-icon" onclick="deleteFile('${doc.id}', 'documents')" title="Delete">
                    <i class="fas fa-trash"></i>
                </div>
                <div class="action-icon" onclick="downloadFile('${doc.id}')" title="Download">
                    <i class="fas fa-download"></i>
                </div>
            </div>
        </div>
    `;
}

function getDocumentIcon(mimetype) {
    if (mimetype.includes('pdf')) return 'fa-file-pdf';
    if (mimetype.includes('word')) return 'fa-file-word';
    if (mimetype.includes('excel')) return 'fa-file-excel';
    if (mimetype.includes('powerpoint')) return 'fa-file-powerpoint';
    if (mimetype.includes('text')) return 'fa-file-alt';
    return 'fa-file';
}

function filterGallery() {
    const sections = document.querySelectorAll('.media-section');
    
    sections.forEach(section => {
        if (currentFilter === 'all') {
            section.style.display = 'block';
        } else {
            const sectionId = section.id;
            if (sectionId.includes(currentFilter)) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        }
    });
}

async function handleUpload(e) {
    e.preventDefault();
    
    const files = document.getElementById('fileInput').files;
    if (files.length === 0) {
        showToast('Please select files to upload', 'warning');
        return;
    }
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showToast('Files uploaded successfully');
            document.getElementById('fileInput').value = '';
            loadGallery(); // Reload gallery
        } else {
            showToast('Error uploading files', 'error');
        }
    } catch (error) {
        console.error('Error uploading files:', error);
        showToast('Error uploading files', 'error');
    } finally {
        hideLoading();
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        showToast(`${files.length} file(s) selected`);
        // automatically upload after selection
        document.getElementById('uploadForm').dispatchEvent(new Event('submit'));
    }
}

async function deleteFile(fileId, type) {
    if (!confirm('Are you sure you want to move this file to trash?')) return;
    
    try {
        const response = await fetch(`/api/files/${fileId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('File moved to trash');
            loadGallery(); // Reload gallery
        } else {
            showToast('Error deleting file', 'error');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showToast('Error deleting file', 'error');
    }
}

async function downloadFile(fileId) {
    try {
        window.location.href = `/api/download/${fileId}`;
    } catch (error) {
        console.error('Error downloading file:', error);
        showToast('Error downloading file', 'error');
    }
}

function showLoading() {
    const container = document.getElementById('galleryContainer');
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