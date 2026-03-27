/**
 * PhysIQ AI - Mobile Dashboard JavaScript
 * Features: Offline support, image compression, pinch-zoom, swipe gestures, pull-to-refresh
 */

// === STATE MANAGEMENT ===
const AppState = {
  currentImage: null,
  generations: [],
  totalCost: 0,
  isOnline: navigator.onLine,
  queuedTransformations: [],
  zoomScale: 1,
  isPullToRefresh: false,
  pullStartY: 0
};

// === DOM ELEMENTS ===
const Elements = {
  uploadArea: null,
  fileInput: null,
  previewContainer: null,
  originalPreview: null,
  resultPreview: null,
  resultLabel: null,
  generateBtn: null,
  loading: null,
  offlineIndicator: null,
  header: null,
  toastContainer: null,
  queuedActions: null,
  pullIndicator: null
};

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
  initializeElements();
  registerServiceWorker();
  setupEventListeners();
  setupOfflineDetection();
  setupPullToRefresh();
  setupPinchZoom();
  setupSwipeGestures();
  checkHealth();
  loadHistory();
  loadQueuedTransformations();
});

function initializeElements() {
  Elements.uploadArea = document.getElementById('uploadArea');
  Elements.fileInput = document.getElementById('fileInput');
  Elements.previewContainer = document.getElementById('previewContainer');
  Elements.originalPreview = document.getElementById('originalPreview');
  Elements.resultPreview = document.getElementById('resultPreview');
  Elements.resultLabel = document.getElementById('resultLabel');
  Elements.generateBtn = document.getElementById('generateBtn');
  Elements.loading = document.getElementById('loading');
  Elements.offlineIndicator = document.getElementById('offlineIndicator');
  Elements.header = document.getElementById('header');
  Elements.toastContainer = document.getElementById('toastContainer');
  Elements.queuedActions = document.getElementById('queuedActions');
  Elements.pullIndicator = document.getElementById('pullIndicator');
}

// === SERVICE WORKER ===
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('SW registered:', reg.scope))
      .catch(err => console.log('SW registration failed:', err));
  }
}

// === OFFLINE SUPPORT ===
function setupOfflineDetection() {
  window.addEventListener('online', () => {
    AppState.isOnline = true;
    updateOfflineUI();
    syncQueuedTransformations();
    showToast('🌐 Back online!', 'success');
  });
  
  window.addEventListener('offline', () => {
    AppState.isOnline = false;
    updateOfflineUI();
    showToast('📴 You\'re offline. Actions will be queued.', 'error');
  });
  
  updateOfflineUI();
}

function updateOfflineUI() {
  Elements.offlineIndicator?.classList.toggle('visible', !AppState.isOnline);
  Elements.header?.classList.toggle('offline-mode', !AppState.isOnline);
}

// === PULL TO REFRESH ===
function setupPullToRefresh() {
  let touchStartY = 0;
  
  document.addEventListener('touchstart', (e) => {
    if (window.scrollY === 0) {
      touchStartY = e.touches[0].clientY;
      AppState.isPullToRefresh = true;
    }
  }, { passive: true });
  
  document.addEventListener('touchmove', (e) => {
    if (!AppState.isPullToRefresh) return;
    const diff = e.touches[0].clientY - touchStartY;
    if (diff > 80) {
      Elements.pullIndicator?.classList.add('visible');
    }
  }, { passive: true });
  
  document.addEventListener('touchend', () => {
    if (Elements.pullIndicator?.classList.contains('visible')) {
      setTimeout(() => {
        Elements.pullIndicator?.classList.remove('visible');
        location.reload();
      }, 500);
    }
    AppState.isPullToRefresh = false;
  });
}

// === IMAGE COMPRESSION (MAX 2MB) ===
async function compressImage(file, maxSizeMB = 2) {
  const maxBytes = maxSizeMB * 1024 * 1024;
  
  // Return original if under size limit
  if (file.size <= maxBytes) return file;
  
  showToast('Compressing image...', 'success');
  
  return new Promise((resolve, reject) => {
    const img = new Image();
    const reader = new FileReader();
    
    reader.onload = (e) => { img.src = e.target.result; };
    reader.onerror = reject;
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      let { width, height } = img;
      
      // Calculate scale to get under 2MB (rough estimate)
      const scale = Math.sqrt(maxBytes / file.size) * 0.9;
      width = Math.floor(width * scale);
      height = Math.floor(height * scale);
      
      canvas.width = width;
      canvas.height = height;
      
      // Draw with high quality
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, width, height);
      
      // Convert to blob with quality optimization
      canvas.toBlob(
        (blob) => resolve(blob || file),
        'image/jpeg',
        0.85
      );
    };
    
    img.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// === EVENT LISTENERS ===
function setupEventListeners() {
  // File upload
  Elements.uploadArea?.addEventListener('click', () => Elements.fileInput?.click());
  
  Elements.uploadArea?.addEventListener('dragover', (e) => {
    e.preventDefault();
    Elements.uploadArea?.classList.add('dragover');
  });
  
  Elements.uploadArea?.addEventListener('dragleave', () => {
    Elements.uploadArea?.classList.remove('dragover');
  });
  
  Elements.uploadArea?.addEventListener('drop', (e) => {
    e.preventDefault();
    Elements.uploadArea?.classList.remove('dragover');
    const file = e.dataTransfer?.files[0];
    if (file) handleFile(file);
  });
  
  Elements.fileInput?.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  });
  
  // Focus areas
  document.getElementById('focusAreas')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('checkbox-item')) {
      e.target.classList.toggle('selected');
    }
  });
  
  // Generate button
  Elements.generateBtn?.addEventListener('click', handleGenerate);
  
  // Modal close on escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });
}

// === FILE HANDLING ===
async function handleFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Please upload an image file', 'error');
    return;
  }
  
  try {
    const compressed = await compressImage(file);
    const reader = new FileReader();
    
    reader.onload = (e) => {
      AppState.currentImage = e.target.result;
      Elements.originalPreview.src = AppState.currentImage;
      Elements.originalPreview.classList.add('has-image');
      Elements.previewContainer.style.display = 'flex';
      Elements.resultPreview.style.display = 'none';
      Elements.resultLabel.textContent = 'Result will appear here';
      Elements.generateBtn.disabled = false;
      showToast('✓ Image ready! Tap Generate', 'success');
    };
    
    reader.readAsDataURL(compressed);
  } catch (err) {
    showToast('Failed to process image', 'error');
    console.error(err);
  }
}

// === SWIPE GESTURES FOR GALLERY ===
function setupSwipeGestures() {
  let startX = 0;
  let isSwiping = false;
  
  Elements.previewContainer?.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
    isSwiping = true;
  }, { passive: true });
  
  Elements.previewContainer?.addEventListener('touchmove', (e) => {
    if (!isSwiping) return;
    const diff = startX - e.touches[0].clientX;
    
    // Prevent default only if horizontal scroll
    if (Math.abs(diff) > 10) {
      e.preventDefault();
    }
  }, { passive: false });
  
  Elements.previewContainer?.addEventListener('touchend', (e) => {
    if (!isSwiping) return;
    const diff = startX - e.changedTouches[0].clientX;
    
    if (Math.abs(diff) > 50) {
      Elements.previewContainer.scrollBy({
        left: diff > 0 ? 200 : -200,
        behavior: 'smooth'
      });
    }
    isSwiping = false;
  }, { passive: true });
}

// === PINCH ZOOM ===
function setupPinchZoom() {
  const containers = [
    { wrapper: document.getElementById('originalWrapper'), img: document.getElementById('modalOriginal') },
    { wrapper: document.getElementById('resultWrapper'), img: document.getElementById('modalResult') }
  ];
  
  containers.forEach(({ wrapper, img }) => {
    if (!wrapper || !img) return;
    
    let pinchStartDist = 0;
    let currentScale = 1;
    
    wrapper.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        pinchStartDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        e.preventDefault();
      }
    }, { passive: false });
    
    wrapper.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const dist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const scale = Math.min(Math.max(currentScale * (dist / pinchStartDist), 1), 5);
        img.style.transform = `scale(${scale})`;
        AppState.zoomScale = scale;
      }
    }, { passive: false });
    
    wrapper.addEventListener('touchend', (e) => {
      if (e.touches.length < 2) {
        currentScale = AppState.zoomScale;
      }
    });
  });
  
  // Double tap to zoom
  containers.forEach(({ wrapper, img }) => {
    let lastTap = 0;
    wrapper?.addEventListener('touchend', (e) => {
      const now = Date.now();
      if (now - lastTap < 300) {
        if (AppState.zoomScale > 1) {
          zoomReset();
        } else {
          zoomIn();
        }
      }
      lastTap = now;
    });
  });
}

function zoomIn() {
  AppState.zoomScale = Math.min(AppState.zoomScale * 1.5, 5);
  updateZoom();
}

function zoomOut() {
  AppState.zoomScale = Math.max(AppState.zoomScale / 1.5, 1);
  updateZoom();
}

function zoomReset() {
  AppState.zoomScale = 1;
  updateZoom();
}

function updateZoom() {
  const imgs = document.querySelectorAll('.modal-image');
  imgs.forEach(img => img.style.transform = `scale(${AppState.zoomScale})`);
}

// === MODAL FUNCTIONS ===
function openModal() {
  const modal = document.getElementById('imageModal');
  if (!modal || !AppState.currentImage) return;
  
  document.getElementById('modalOriginal').src = Elements.originalPreview.src;
  document.getElementById('modalResult').src = Elements.resultPreview.src;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const modal = document.getElementById('imageModal');
  modal?.classList.remove('active');
  document.body.style.overflow = '';
  zoomReset();
}

// === GENERATION HANDLING ===
async function handleGenerate() {
  if (!AppState.currentImage) return;
  
  // Check if offline
  if (!AppState.isOnline) {
    queueTransformation();
    return;
  }
  
  Elements.generateBtn.disabled = true;
  Elements.loading.classList.add('active');
  
  const startTime = Date.now();
  const loadingDetail = document.getElementById('loadingDetail');
  
  const updateLoading = setInterval(() => {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    if (loadingDetail) loadingDetail.textContent = `${elapsed}s elapsed...`;
  }, 1000);
  
  try {
    const profile = getProfile();
    const horizonWeeks = parseInt(document.getElementById('horizon').value);
    
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: AppState.currentImage, profile, horizonWeeks })
    });
    
    clearInterval(updateLoading);
    const data = await res.json();
    
    if (data.success) {
      displayResult(data.data);
      showToast('✓ Transformation complete!', 'success');
    } else {
      throw new Error(data.error || 'Generation failed');
    }
  } catch (err) {
    clearInterval(updateLoading);
    showToast(err.message, 'error');
    
    // Queue if network error
    if (!navigator.onLine || err.message.includes('fetch')) {
      queueTransformation();
    }
  } finally {
    Elements.loading.classList.remove('active');
    Elements.generateBtn.disabled = false;
    if (loadingDetail) loadingDetail.textContent = 'This takes 25-40 seconds';
  }
}

function getProfile() {
  const weightLbs = parseInt(document.getElementById('weight').value);
  return {
    age: parseInt(document.getElementById('age').value),
    gender: document.getElementById('gender').value,
    weightKg: Math.round(weightLbs * 0.453592),
    weightLbs: weightLbs,
    bodyFatPercent: parseInt(document.getElementById('bodyFat').value),
    experienceLevel: document.getElementById('experience').value,
    workoutsPerWeek: parseInt(document.getElementById('workouts').value),
    sleepQuality: document.getElementById('sleep').value,
    nutritionGoal: document.getElementById('nutrition').value,
    focusAreas: getSelectedFocusAreas()
  };
}

function getSelectedFocusAreas() {
  return Array.from(document.querySelectorAll('#focusAreas .checkbox-item.selected'))
    .map(item => item.dataset.value);
}

function queueTransformation() {
  const transformation = {
    image: AppState.currentImage,
    profile: getProfile(),
    horizonWeeks: parseInt(document.getElementById('horizon').value),
    timestamp: Date.now(),
    id: 'queued_' + Date.now()
  };
  
  AppState.queuedTransformations.push(transformation);
  localStorage.setItem('queuedTransformations', JSON.stringify(AppState.queuedTransformations));
  
  updateQueuedUI();
  showToast('⏳ Queued for when you\'re back online', 'success');
}

function updateQueuedUI() {
  if (AppState.queuedTransformations.length > 0) {
    Elements.queuedActions?.classList.add('visible');
    document.getElementById('queuedActionsList').textContent = 
      `${AppState.queuedTransformations.length} transformation(s) queued`;
  } else {
    Elements.queuedActions?.classList.remove('visible');
  }
}

async function syncQueuedTransformations() {
  if (AppState.queuedTransformations.length === 0) return;
  
  showToast('🔄 Syncing queued transformations...', 'success');
  
  const toSync = [...AppState.queuedTransformations];
  const synced = [];
  
  for (const t of toSync) {
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: t.image, profile: t.profile, horizonWeeks: t.horizonWeeks })
      });
      
      if (res.ok) {
        synced.push(t.id);
      }
    } catch (err) {
      console.error('Sync failed for:', t.id);
    }
  }
  
  // Remove synced items
  AppState.queuedTransformations = AppState.queuedTransformations.filter(
    t => !synced.includes(t.id)
  );
  
  localStorage.setItem('queuedTransformations', JSON.stringify(AppState.queuedTransformations));
  updateQueuedUI();
  
  if (synced.length > 0) {
    showToast(`✓ ${synced.length} transformation(s) synced!`, 'success');
  }
}

function loadQueuedTransformations() {
  const saved = localStorage.getItem('queuedTransformations');
  if (saved) {
    AppState.queuedTransformations = JSON.parse(saved);
    updateQueuedUI();
  }
}

// === DISPLAY FUNCTIONS ===
function displayResult(data) {
  Elements.resultPreview.src = data.imageUrl;
  Elements.resultPreview.style.display = 'block';
  Elements.resultPreview.classList.add('has-image');
  Elements.resultLabel.textContent = `${data.horizonWeeks} week projection`;
  
  renderCalculations(data.projections);
  renderUserExplanation(data);
  
  const promptPanel = document.getElementById('promptPanel');
  if (promptPanel) {
    promptPanel.innerHTML = `<pre style="white-space: pre-wrap; color: #999;">${escapeHtml(data.prompt)}</pre>`;
  }
  
  document.getElementById('statTime').textContent = data.elapsedSec;
  document.getElementById('statCost').textContent = data.cost.toFixed(2);
  document.getElementById('statModel').textContent = 'Flux';
  document.getElementById('statConfidence').textContent = data.projections.confidence.level.toUpperCase();
  
  // Update history
  data.originalImage = AppState.currentImage;
  AppState.generations.push(data);
  AppState.totalCost += data.cost;
  document.getElementById('totalCost').textContent = AppState.totalCost.toFixed(2);
  renderHistory();
}

function renderCalculations(projections) {
  const container = document.getElementById('calculationSteps');
  if (!container) return;
  
  let html = `
    <div style="margin-bottom: 15px; padding: 10px; background: #1a1a1a; border-radius: 8px;">
      <div style="color: #4ade80; font-size: 18px; font-weight: bold;">
        Projected Gain: ${projections.totalGainLbs.toFixed(1)} lbs
      </div>
      <div style="color: #888; font-size: 13px; margin-top: 4px;">
        (${projections.totalGainKg.toFixed(2)} kg over ${projections.horizonWeeks} weeks)
      </div>
    </div>
  `;
  
  projections.steps?.forEach(step => {
    html += `
      <div class="step-item">
        <div class="step-name">Step ${step.step}: ${step.name}</div>
        <div class="step-calc">${step.calculation}</div>
        <div class="step-source">📚 ${step.source}</div>
      </div>
    `;
  });
  
  container.innerHTML = html;
}

function renderUserExplanation(data) {
  const container = document.getElementById('userExplanation');
  if (!container) return;
  
  const { profile, projections, horizonWeeks } = data;
  const timeDesc = horizonWeeks <= 12 ? `${horizonWeeks} weeks` : `${Math.round(horizonWeeks / 4)} months`;
  
  let html = `
    <div style="background: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
      <div style="font-size: 20px; font-weight: bold; color: #4ade80; margin-bottom: 10px;">
        Projected: +${projections.totalGainLbs.toFixed(1)} lbs lean muscle in ${timeDesc}
      </div>
      <div style="color: #888;">Based on your profile and peer-reviewed exercise science research</div>
    </div>
    <ul style="color: #ccc; margin-left: 20px;">
  `;
  
  // Add experience-based explanation
  if (profile.experienceLevel === 'beginner') {
    html += `<li><strong>Beginner advantage:</strong> You're in the "newbie gains" window where muscle growth is fastest (1-1.5% bodyweight/month potential).</li>`;
  } else if (profile.experienceLevel === 'intermediate') {
    html += `<li><strong>Intermediate lifter:</strong> Gains slow down after the first year (0.5-1% bodyweight/month).</li>`;
  } else {
    html += `<li><strong>Advanced lifter:</strong> You're approaching your genetic ceiling. Expect subtle refinement (0.25-0.5% bodyweight/month).</li>`;
  }
  
  html += `</ul>`;
  container.innerHTML = html;
}

function renderHistory() {
  const list = document.getElementById('historyList');
  if (!list) return;
  
  if (AppState.generations.length === 0) {
    list.innerHTML = '<p style="color: #666;">No generations yet</p>';
    return;
  }
  
  list.innerHTML = AppState.generations.slice(-5).reverse().map((g, idx) => `
    <div class="history-item" onclick="openHistoryModal(${AppState.generations.length - 1 - idx})">
      <img src="${g.originalImage || ''}" alt="Before">
      <img src="${g.imageUrl}" alt="After">
      <div class="history-info">
        <div class="history-id">${g.id}</div>
        <div class="history-meta">${g.horizonWeeks} weeks • ${g.elapsedSec}s • $${g.cost.toFixed(2)}</div>
      </div>
    </div>
  `).join('');
}

function openHistoryModal(index) {
  const g = AppState.generations[index];
  if (!g) return;
  
  document.getElementById('modalOriginal').src = g.originalImage || '';
  document.getElementById('modalResult').src = g.imageUrl;
  document.getElementById('imageModal').classList.add('active');
}

// === UTILITY FUNCTIONS ===
function showToast(message, type = 'success') {
  const container = Elements.toastContainer;
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  
  requestAnimationFrame(() => toast.classList.add('visible'));
  
  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    
    const serverStatus = document.getElementById('serverStatus');
    const falStatus = document.getElementById('falStatus');
    const googleStatus = document.getElementById('googleStatus');
    
    if (serverStatus) serverStatus.className = 'status-dot green';
    if (falStatus) falStatus.className = data.apiKeys?.fal?.includes('✓') ? 'status-dot green' : 'status-dot red';
    if (googleStatus) googleStatus.className = data.apiKeys?.google?.includes('✓') ? 'status-dot green' : 'status-dot red';
  } catch (e) {
    const serverStatus = document.getElementById('serverStatus');
    if (serverStatus) serverStatus.className = 'status-dot red';
  }
}

async function loadHistory() {
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    AppState.generations = data.generations || [];
    AppState.totalCost = data.costs?.total || 0;
    
    const totalCostEl = document.getElementById('totalCost');
    if (totalCostEl) totalCostEl.textContent = AppState.totalCost.toFixed(2);
    
    renderHistory();
  } catch (e) {
    console.error('Failed to load history', e);
  }
}
