/**
 * PhysiqAI - Enhanced Upload Module with Image Compression
 * Handles file uploads with automatic image compression for mobile optimization
 */

const UploadManager = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        maxWidth: 1920,        // Max width after compression
        maxHeight: 1920,       // Max height after compression
        quality: 0.85,         // JPEG quality
        mobileMaxWidth: 1200,  // Smaller size for mobile
        mobileQuality: 0.80,   // Lower quality for mobile
        maxFileSize: 10 * 1024 * 1024, // 10MB
        chunkSize: 1024 * 1024 // 1MB chunks for large uploads
    };

    // State
    const state = {
        uploads: new Map(),    // Store upload states
        compressedFiles: new Map(),
        isMobile: detectMobile()
    };

    /**
     * Detect if user is on mobile device
     */
    function detectMobile() {
        const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
        const isTouch = window.matchMedia('(pointer: coarse)').matches;
        const isSmallScreen = window.innerWidth < 768;
        return mobileRegex.test(navigator.userAgent) || isTouch || isSmallScreen;
    }

    /**
     * Create loading overlay for upload
     */
    function createLoadingOverlay(message = 'Processing...') {
        let overlay = document.getElementById('upload-loading-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'upload-loading-overlay';
            overlay.innerHTML = `
                <div class="upload-loading-content">
                    <div class="upload-spinner"></div>
                    <p class="upload-loading-text">${message}</p>
                    <div class="upload-progress-bar">
                        <div class="upload-progress-fill"></div>
                    </div>
                </div>
            `;
            overlay.className = 'upload-loading-overlay';
            document.body.appendChild(overlay);
        } else {
            overlay.querySelector('.upload-loading-text').textContent = message;
        }
        
        return overlay;
    }

    /**
     * Show loading overlay
     */
    function showLoading(message) {
        const overlay = createLoadingOverlay(message);
        overlay.classList.add('active');
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        const overlay = document.getElementById('upload-loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    /**
     * Update loading progress
     */
    function updateLoadingProgress(percent) {
        const fill = document.querySelector('.upload-progress-fill');
        if (fill) {
            fill.style.width = percent + '%';
        }
    }

    /**
     * Compress image file
     * @param {File} file - Original image file
     * @param {Object} options - Compression options
     * @returns {Promise<File>} Compressed file
     */
    async function compressImage(file, options = {}) {
        const isMobile = state.isMobile;
        const maxWidth = options.maxWidth || (isMobile ? CONFIG.mobileMaxWidth : CONFIG.maxWidth);
        const maxHeight = options.maxHeight || (isMobile ? CONFIG.mobileMaxWidth : CONFIG.maxHeight);
        const quality = options.quality || (isMobile ? CONFIG.mobileQuality : CONFIG.quality);
        
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const img = new Image();
                
                img.onload = () => {
                    // Calculate new dimensions
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > height) {
                        if (width > maxWidth) {
                            height = (height * maxWidth) / width;
                            width = maxWidth;
                        }
                    } else {
                        if (height > maxHeight) {
                            width = (width * maxHeight) / height;
                            height = maxHeight;
                        }
                    }
                    
                    // Create canvas
                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    
                    const ctx = canvas.getContext('2d');
                    
                    // Better image rendering
                    ctx.imageSmoothingEnabled = true;
                    ctx.imageSmoothingQuality = 'high';
                    
                    // Draw image
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    // Convert to blob
                    canvas.toBlob((blob) => {
                        if (!blob) {
                            reject(new Error('Canvas to Blob conversion failed'));
                            return;
                        }
                        
                        // Create new file
                        const compressedFile = new File([blob], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });
                        
                        console.log(`Compressed ${file.name}: ${(file.size / 1024).toFixed(1)}KB → ${(compressedFile.size / 1024).toFixed(1)}KB (${((1 - compressedFile.size / file.size) * 100).toFixed(0)}% reduction)`);
                        
                        resolve(compressedFile);
                    }, 'image/jpeg', quality);
                };
                
                img.onerror = () => reject(new Error('Failed to load image'));
                img.src = e.target.result;
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsDataURL(file);
        });
    }

    /**
     * Process file upload with compression
     * @param {File} file - Original file
     * @param {string} uploadId - Unique upload identifier
     */
    async function processUpload(file, uploadId) {
        showLoading('Compressing image...');
        updateLoadingProgress(20);
        
        try {
            // Validate file
            const validation = Validation.validatePhoto(file);
            if (!validation.valid) {
                throw new Error(validation.message);
            }
            
            updateLoadingProgress(40);
            
            // Compress image
            let processedFile = file;
            
            // Only compress if file is large or on mobile
            if (file.size > 500 * 1024 || state.isMobile) {
                processedFile = await compressImage(file);
            }
            
            updateLoadingProgress(70);
            state.compressedFiles.set(uploadId, processedFile);
            
            updateLoadingProgress(100);
            
            // Small delay for UX
            await new Promise(resolve => setTimeout(resolve, 300));
            
            hideLoading();
            
            return {
                success: true,
                file: processedFile,
                originalSize: file.size,
                compressedSize: processedFile.size,
                reduction: ((1 - processedFile.size / file.size) * 100).toFixed(0)
            };
            
        } catch (error) {
            hideLoading();
            console.error('Upload processing error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Handle file input change
     * @param {HTMLInputElement} input - File input element
     * @param {Object} callbacks - Callback functions
     */
    function handleFileSelect(input, callbacks = {}) {
        const file = input.files[0];
        if (!file) return;
        
        const uploadId = input.id || Date.now().toString();
        
        processUpload(file, uploadId).then(result => {
            if (result.success) {
                // Update preview
                const preview = input.closest('.upload-zone')?.querySelector('.upload-preview');
                if (preview) {
                    const img = preview.querySelector('img');
                    if (img) {
                        img.src = URL.createObjectURL(result.file);
                    }
                    preview.hidden = false;
                }
                
                // Update placeholder
                const placeholder = input.closest('.upload-zone')?.querySelector('.upload-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
                
                if (callbacks.onSuccess) {
                    callbacks.onSuccess(result);
                }
            } else {
                // Show error
                alert(result.error);
                input.value = '';
                
                if (callbacks.onError) {
                    callbacks.onError(result.error);
                }
            }
        });
    }

    /**
     * Handle file drop
     * @param {DragEvent} e - Drop event
     * @param {HTMLElement} zone - Drop zone element
     * @param {Object} callbacks - Callback functions
     */
    function handleFileDrop(e, zone, callbacks = {}) {
        e.preventDefault();
        e.stopPropagation();
        
        zone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length === 0) return;
        
        const file = files[0];
        const input = zone.querySelector('input[type="file"]');
        
        // Create DataTransfer to set files on input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        input.files = dataTransfer.files;
        
        handleFileSelect(input, callbacks);
    }

    /**
     * Initialize upload zones
     */
    function initUploadZones() {
        const zones = document.querySelectorAll('.upload-zone');
        
        zones.forEach(zone => {
            const input = zone.querySelector('input[type="file"]');
            const removeBtn = zone.querySelector('.upload-remove');
            const preview = zone.querySelector('.upload-preview');
            const placeholder = zone.querySelector('.upload-placeholder');
            
            if (!input) return;
            
            // Click to upload
            zone.addEventListener('click', (e) => {
                if (e.target === zone || e.target.closest('.upload-placeholder') || e.target.closest('.upload-icon')) {
                    input.click();
                }
            });
            
            // File selection
            input.addEventListener('change', () => {
                handleFileSelect(input, {
                    onSuccess: () => updateUploadProgress(),
                    onError: () => updateUploadProgress()
                });
            });
            
            // Drag & drop
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('dragover');
            });
            
            zone.addEventListener('dragleave', () => {
                zone.classList.remove('dragover');
            });
            
            zone.addEventListener('drop', (e) => {
                handleFileDrop(e, zone, {
                    onSuccess: () => updateUploadProgress(),
                    onError: () => updateUploadProgress()
                });
            });
            
            // Remove button
            if (removeBtn) {
                removeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    input.value = '';
                    if (preview) preview.hidden = true;
                    if (placeholder) placeholder.style.display = 'flex';
                    updateUploadProgress();
                });
            }
        });
    }

    /**
     * Update upload progress
     */
    function updateUploadProgress() {
        const inputs = document.querySelectorAll('.upload-zone input[type="file"]');
        let count = 0;
        
        inputs.forEach(input => {
            if (input.files.length > 0) count++;
        });
        
        // Update progress bar
        const progressFill = document.getElementById('progressFill');
        const uploadCount = document.getElementById('uploadCount');
        const processBtn = document.getElementById('processBtn');
        
        if (progressFill) {
            const percent = (count / inputs.length) * 100;
            progressFill.style.width = percent + '%';
        }
        
        if (uploadCount) {
            uploadCount.textContent = count;
        }
        
        if (processBtn) {
            processBtn.disabled = count < inputs.length;
        }
    }

    /**
     * Get all compressed files
     */
    function getCompressedFiles() {
        return Array.from(state.compressedFiles.values());
    }

    /**
     * Clear all uploads
     */
    function clearUploads() {
        state.compressedFiles.clear();
        state.uploads.clear();
        
        const inputs = document.querySelectorAll('.upload-zone input[type="file"]');
        inputs.forEach(input => {
            input.value = '';
        });
        
        const previews = document.querySelectorAll('.upload-preview');
        previews.forEach(preview => {
            preview.hidden = true;
        });
        
        const placeholders = document.querySelectorAll('.upload-placeholder');
        placeholders.forEach(placeholder => {
            placeholder.style.display = 'flex';
        });
        
        updateUploadProgress();
    }

    // Public API
    return {
        compressImage,
        processUpload,
        handleFileSelect,
        handleFileDrop,
        initUploadZones,
        getCompressedFiles,
        clearUploads,
        showLoading,
        hideLoading,
        updateLoadingProgress,
        isMobile: () => state.isMobile
    };
})();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    UploadManager.initUploadZones();
    
    // Add CSS for loading overlay if not present
    if (!document.getElementById('upload-loading-styles')) {
        const style = document.createElement('style');
        style.id = 'upload-loading-styles';
        style.textContent = `
            .upload-loading-overlay {
                position: fixed;
                inset: 0;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(15, 15, 26, 0.95);
                backdrop-filter: blur(10px);
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s ease, visibility 0.3s ease;
            }
            
            .upload-loading-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            
            .upload-loading-content {
                text-align: center;
                padding: 2rem;
            }
            
            .upload-spinner {
                width: 56px;
                height: 56px;
                margin: 0 auto 1.5rem;
                border: 4px solid var(--bg-tertiary);
                border-top-color: var(--primary);
                border-radius: 50%;
                animation: upload-spin 1s linear infinite;
            }
            
            @keyframes upload-spin {
                to { transform: rotate(360deg); }
            }
            
            .upload-loading-text {
                font-size: 1rem;
                color: var(--text-secondary);
                margin-bottom: 1rem;
            }
            
            .upload-progress-bar {
                width: 200px;
                height: 4px;
                margin: 0 auto;
                background: var(--bg-tertiary);
                border-radius: 2px;
                overflow: hidden;
            }
            
            .upload-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary), var(--primary-light));
                border-radius: 2px;
                transition: width 0.2s ease;
                width: 0%;
            }
            
            @media (max-width: 768px) {
                .upload-loading-content {
                    padding: 1.5rem;
                }
                
                .upload-spinner {
                    width: 48px;
                    height: 48px;
                    border-width: 3px;
                }
                
                .upload-loading-text {
                    font-size: 0.875rem;
                }
                
                .upload-progress-bar {
                    width: 160px;
                }
            }
        `;
        document.head.appendChild(style);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UploadManager;
}
