// ========================================
// PhysiqAI - Main App JavaScript
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize error handler first
    if (typeof ErrorHandler !== 'undefined') {
        ErrorHandler.init();
    }
    
    initNavigation();
    initUploadPage();
});

// Navigation
function initNavigation() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }
}

// Upload Page
function initUploadPage() {
    const uploadZones = document.querySelectorAll('.upload-zone');
    const processBtn = document.getElementById('processBtn');
    const progressFill = document.getElementById('progressFill');
    const uploadCount = document.getElementById('uploadCount');
    
    let uploadedFiles = {
        front: null,
        side: null,
        back: null
    };
    
    uploadZones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        const placeholder = zone.querySelector('.upload-placeholder');
        const preview = zone.querySelector('.upload-preview');
        const previewImg = preview?.querySelector('img');
        const removeBtn = zone.querySelector('.upload-remove');
        const viewType = zone.id.replace('upload', '').toLowerCase();
        
        // Click to upload
        zone.addEventListener('click', (e) => {
            if (e.target !== removeBtn && !removeBtn?.contains(e.target)) {
                input?.click();
            }
        });
        
        // File input change
        input?.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleFile(file, viewType, zone, preview, previewImg, placeholder);
        });
        
        // Drag and drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                handleFile(file, viewType, zone, preview, previewImg, placeholder);
            }
        });
        
        // Remove button
        removeBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            uploadedFiles[viewType] = null;
            preview.hidden = true;
            placeholder.hidden = false;
            input.value = '';
            updateProgress();
        });
    });
    
    async function handleFile(file, viewType, zone, preview, previewImg, placeholder) {
        // Use ErrorHandler for validation if available
        if (typeof ErrorHandler !== 'undefined') {
            const validation = ErrorHandler.upload.validate(file);
            
            if (!validation.valid) {
                ErrorHandler.showUserMessage(validation.error, 'error');
                const input = zone.querySelector('input[type="file"]');
                input.value = '';
                return;
            }
            
            try {
                const dataUrl = await ErrorHandler.upload.readAsDataURL(file);
                uploadedFiles[viewType] = file;
                previewImg.src = dataUrl;
                preview.hidden = false;
                placeholder.hidden = true;
                updateProgress();
                ErrorHandler.showUserMessage(
                    `${viewType.charAt(0).toUpperCase() + viewType.slice(1)} view uploaded successfully!`, 
                    'success', 
                    { duration: 2000 }
                );
            } catch (error) {
                ErrorHandler.showUserMessage(`Failed to load ${viewType} view: ${error.message}`, 'error');
            }
        } else {
            // Fallback validation
            if (!file.type.startsWith('image/')) {
                alert('Please upload an image file');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                alert('File size must be less than 10MB');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                uploadedFiles[viewType] = file;
                previewImg.src = e.target.result;
                preview.hidden = false;
                placeholder.hidden = true;
                updateProgress();
            };
            reader.onerror = () => {
                alert('Failed to read file. Please try again.');
            };
            reader.readAsDataURL(file);
        }
    }
    
    function updateProgress() {
        const count = Object.values(uploadedFiles).filter(f => f !== null).length;
        const percent = (count / 3) * 100;
        
        if (progressFill) progressFill.style.width = `${percent}%`;
        if (uploadCount) uploadCount.textContent = count;
        if (processBtn) processBtn.disabled = count < 1;
    }
    
    // Process button
    processBtn?.addEventListener('click', () => {
        const modal = document.getElementById('processingModal');
        if (modal) {
            modal.hidden = false;
            simulateProcessing();
        }
    });
    
    function simulateProcessing() {
        const steps = document.querySelectorAll('.step');
        let currentStep = 0;
        
        const interval = setInterval(() => {
            if (currentStep > 0) {
                steps[currentStep - 1].classList.remove('active');
                steps[currentStep - 1].classList.add('completed');
            }
            
            if (currentStep < steps.length) {
                steps[currentStep].classList.add('active');
                currentStep++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    window.location.href = 'avatar.html';
                }, 500);
            }
        }, 1500);
    }
}
