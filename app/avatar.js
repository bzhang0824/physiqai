// ========================================
// PhysiqAI - 3D Avatar Viewer (Three.js)
// Mobile-Optimized with LOD, Touch Gestures, Performance Enhancements
// ========================================

let scene, camera, renderer, avatarGroup;
let isRotating = false;
let isWireframe = false;
let isMobile = false;
let lodLevel = 'high'; // 'high', 'medium', 'low'
let touchState = {
    isDragging: false,
    isPinching: false,
    startDistance: 0,
    startZoom: 5,
    lastTouchTime: 0,
    touches: []
};

// Loading state management
const loadingManager = {
    isLoading: false,
    progress: 0,
    startTime: 0,
    show() {
        const loader = document.getElementById('loading-overlay');
        if (loader) loader.classList.add('active');
        this.isLoading = true;
        this.startTime = Date.now();
    },
    hide() {
        // Ensure minimum loading time for smooth UX
        const elapsed = Date.now() - this.startTime;
        const minTime = 500;
        const delay = Math.max(0, minTime - elapsed);
        
        setTimeout(() => {
            const loader = document.getElementById('loading-overlay');
            if (loader) loader.classList.remove('active');
            this.isLoading = false;
        }, delay);
    },
    updateProgress(percent) {
        this.progress = percent;
        const progressEl = document.getElementById('loading-progress');
        if (progressEl) progressEl.style.width = percent + '%';
    }
};

// Detect mobile device
function detectMobile() {
    const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
    const isTouch = window.matchMedia('(pointer: coarse)').matches;
    const isSmallScreen = window.innerWidth < 768;
    return mobileRegex.test(navigator.userAgent) || isTouch || isSmallScreen;
}

// LOD Configuration based on distance/screen size
const LOD_CONFIG = {
    high: {
        head: [32, 32],
        neck: [16, 1],
        torso: [32, 1],
        chest: [32, 1],
        shoulder: [16, 16],
        arm: [16, 1],
        elbow: [16, 16],
        forearm: [16, 1],
        hand: null, // BoxGeometry
        hip: [32, 1],
        leg: [16, 1],
        knee: [16, 16],
        lowerLeg: [16, 1],
        foot: null, // BoxGeometry
        ground: [64, 1]
    },
    medium: {
        head: [20, 20],
        neck: [12, 1],
        torso: [20, 1],
        chest: [20, 1],
        shoulder: [12, 12],
        arm: [12, 1],
        elbow: [12, 12],
        forearm: [12, 1],
        hand: null,
        hip: [20, 1],
        leg: [12, 1],
        knee: [12, 12],
        lowerLeg: [12, 1],
        foot: null,
        ground: [32, 1]
    },
    low: {
        head: [12, 12],
        neck: [8, 1],
        torso: [12, 1],
        chest: [12, 1],
        shoulder: [8, 8],
        arm: [8, 1],
        elbow: [8, 8],
        forearm: [8, 1],
        hand: null,
        hip: [12, 1],
        leg: [8, 1],
        knee: [8, 8],
        lowerLeg: [8, 1],
        foot: null,
        ground: [16, 1]
    }
};

// Image compression utility
async function compressImage(file, maxWidth = 1200, quality = 0.85) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                // Calculate new dimensions
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob((blob) => {
                    resolve(new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    }));
                }, 'image/jpeg', quality);
            };
            img.onerror = reject;
            img.src = e.target.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Initialize with error handling and fallback
if (typeof ErrorHandler !== 'undefined') {
    ErrorHandler.viewer3D.initWithFallback('three-canvas', () => {
        init();
        animate();
        return true;
    }, {
        placeholderImage: '/assets/avatar-placeholder.svg'
    });
} else {
    init();
    animate();
}

function init() {
    loadingManager.show();
    
    const container = document.getElementById('three-canvas');
    if (!container) {
        loadingManager.hide();
        if (typeof ErrorHandler !== 'undefined') {
            ErrorHandler.showUserMessage('3D viewer container not found', 'error');
        }
        return;
    }
    
    // Detect mobile and set flags
    isMobile = detectMobile();
    
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f0f1a);
    
    // Fog only on desktop for performance
    if (!isMobile) {
        scene.fog = new THREE.Fog(0x0f0f1a, 10, 50);
    }
    
    // Camera setup
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 1, 5);
    
    // Renderer setup with mobile optimizations
    renderer = new THREE.WebGLRenderer({ 
        antialias: !isMobile, // Disable antialias on mobile
        powerPreference: isMobile ? 'low-power' : 'high-performance',
        alpha: false
    });
    
    // Limit pixel ratio on mobile for performance
    const pixelRatio = isMobile ? Math.min(window.devicePixelRatio, 2) : window.devicePixelRatio;
    renderer.setPixelRatio(pixelRatio);
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    
    // Shadows - disabled on mobile
    if (!isMobile) {
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }
    
    container.appendChild(renderer.domElement);
    
    // Lighting - simplified on mobile
    setupLighting();
    
    // Create procedural avatar with LOD
    updateLOD();
    createAvatar();
    createEnvironment();
    
    // Controls
    setupControls();
    
    // Resize handler with debounce
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(onWindowResize, 100);
    });
    
    // Visibility change for performance
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Lazy load non-critical resources
    lazyLoadResources();
    
    loadingManager.updateProgress(100);
    loadingManager.hide();
}

function setupLighting() {
    // Ambient light - always on
    const ambientLight = new THREE.AmbientLight(0xffffff, isMobile ? 0.6 : 0.4);
    scene.add(ambientLight);
    
    // Key light - simplified on mobile
    const keyLight = new THREE.DirectionalLight(0x6366f1, isMobile ? 0.8 : 1);
    keyLight.position.set(5, 5, 5);
    
    if (!isMobile) {
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
    }
    scene.add(keyLight);
    
    // Skip fill and rim lights on mobile for performance
    if (!isMobile) {
        const fillLight = new THREE.DirectionalLight(0x10b981, 0.5);
        fillLight.position.set(-5, 0, 5);
        scene.add(fillLight);
        
        const rimLight = new THREE.SpotLight(0xffffff, 0.8);
        rimLight.position.set(0, 5, -5);
        rimLight.lookAt(0, 0, 0);
        scene.add(rimLight);
    }
}

function updateLOD() {
    // Determine LOD level based on screen size and mobile status
    const width = window.innerWidth;
    const cameraDist = camera ? camera.position.z : 5;
    
    if (isMobile || width < 414 || cameraDist > 6) {
        lodLevel = 'low';
    } else if (width < 768 || cameraDist > 4) {
        lodLevel = 'medium';
    } else {
        lodLevel = 'high';
    }
}

function createAvatar() {
    if (avatarGroup) {
        scene.remove(avatarGroup);
    }
    
    avatarGroup = new THREE.Group();
    const config = LOD_CONFIG[lodLevel];
    
    // Material - simplified on mobile
    const bodyMaterial = new THREE.MeshStandardMaterial({
        color: 0x6366f1,
        metalness: isMobile ? 0.1 : 0.3,
        roughness: isMobile ? 0.6 : 0.4,
        emissive: 0x1a1a3e,
        emissiveIntensity: isMobile ? 0.1 : 0.2
    });
    
    const jointMaterial = new THREE.MeshStandardMaterial({
        color: 0x4f46e5,
        metalness: isMobile ? 0.2 : 0.5,
        roughness: isMobile ? 0.5 : 0.3
    });
    
    // Head
    const headGeo = new THREE.SphereGeometry(0.25, ...config.head);
    const head = new THREE.Mesh(headGeo, bodyMaterial);
    head.position.y = 1.7;
    if (!isMobile) head.castShadow = true;
    avatarGroup.add(head);
    
    // Neck
    const neckGeo = new THREE.CylinderGeometry(0.1, 0.12, 0.15, ...config.neck);
    const neck = new THREE.Mesh(neckGeo, jointMaterial);
    neck.position.y = 1.5;
    if (!isMobile) neck.castShadow = true;
    avatarGroup.add(neck);
    
    // Torso
    const torsoGeo = new THREE.CylinderGeometry(0.3, 0.25, 0.7, ...config.torso);
    const torso = new THREE.Mesh(torsoGeo, bodyMaterial);
    torso.position.y = 1.05;
    if (!isMobile) torso.castShadow = true;
    avatarGroup.add(torso);
    
    // Chest
    const chestGeo = new THREE.CylinderGeometry(0.35, 0.3, 0.4, ...config.chest);
    const chest = new THREE.Mesh(chestGeo, bodyMaterial);
    chest.position.y = 1.2;
    if (!isMobile) chest.castShadow = true;
    avatarGroup.add(chest);
    
    // Shoulders
    const shoulderGeo = new THREE.SphereGeometry(0.15, ...config.shoulder);
    
    const leftShoulder = new THREE.Mesh(shoulderGeo, jointMaterial);
    leftShoulder.position.set(-0.4, 1.35, 0);
    avatarGroup.add(leftShoulder);
    
    const rightShoulder = new THREE.Mesh(shoulderGeo, jointMaterial);
    rightShoulder.position.set(0.4, 1.35, 0);
    avatarGroup.add(rightShoulder);
    
    // Arms
    const armGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.6, ...config.arm);
    
    const leftArm = new THREE.Mesh(armGeo, bodyMaterial);
    leftArm.position.set(-0.45, 1.0, 0);
    leftArm.rotation.z = 0.1;
    if (!isMobile) leftArm.castShadow = true;
    avatarGroup.add(leftArm);
    
    const rightArm = new THREE.Mesh(armGeo, bodyMaterial);
    rightArm.position.set(0.45, 1.0, 0);
    rightArm.rotation.z = -0.1;
    if (!isMobile) rightArm.castShadow = true;
    avatarGroup.add(rightArm);
    
    // Elbows
    const elbowGeo = new THREE.SphereGeometry(0.09, ...config.elbow);
    
    const leftElbow = new THREE.Mesh(elbowGeo, jointMaterial);
    leftElbow.position.set(-0.48, 0.7, 0);
    avatarGroup.add(leftElbow);
    
    const rightElbow = new THREE.Mesh(elbowGeo, jointMaterial);
    rightElbow.position.set(0.48, 0.7, 0);
    avatarGroup.add(rightElbow);
    
    // Forearms
    const forearmGeo = new THREE.CylinderGeometry(0.07, 0.06, 0.5, ...config.forearm);
    
    const leftForearm = new THREE.Mesh(forearmGeo, bodyMaterial);
    leftForearm.position.set(-0.5, 0.4, 0.1);
    leftForearm.rotation.x = -0.3;
    if (!isMobile) leftForearm.castShadow = true;
    avatarGroup.add(leftForearm);
    
    const rightForearm = new THREE.Mesh(forearmGeo, bodyMaterial);
    rightForearm.position.set(0.5, 0.4, 0.1);
    rightForearm.rotation.x = -0.3;
    if (!isMobile) rightForearm.castShadow = true;
    avatarGroup.add(rightForearm);
    
    // Hands
    const handGeo = new THREE.BoxGeometry(0.12, 0.15, 0.05);
    
    const leftHand = new THREE.Mesh(handGeo, jointMaterial);
    leftHand.position.set(-0.52, 0.1, 0.15);
    avatarGroup.add(leftHand);
    
    const rightHand = new THREE.Mesh(handGeo, jointMaterial);
    rightHand.position.set(0.52, 0.1, 0.15);
    avatarGroup.add(rightHand);
    
    // Hips
    const hipGeo = new THREE.CylinderGeometry(0.26, 0.28, 0.25, ...config.hip);
    const hips = new THREE.Mesh(hipGeo, bodyMaterial);
    hips.position.y = 0.55;
    if (!isMobile) hips.castShadow = true;
    avatarGroup.add(hips);
    
    // Legs
    const legGeo = new THREE.CylinderGeometry(0.12, 0.1, 0.7, ...config.leg);
    
    const leftLeg = new THREE.Mesh(legGeo, bodyMaterial);
    leftLeg.position.set(-0.15, 0.1, 0);
    if (!isMobile) leftLeg.castShadow = true;
    avatarGroup.add(leftLeg);
    
    const rightLeg = new THREE.Mesh(legGeo, bodyMaterial);
    rightLeg.position.set(0.15, 0.1, 0);
    if (!isMobile) rightLeg.castShadow = true;
    avatarGroup.add(rightLeg);
    
    // Knees
    const kneeGeo = new THREE.SphereGeometry(0.11, ...config.knee);
    
    const leftKnee = new THREE.Mesh(kneeGeo, jointMaterial);
    leftKnee.position.set(-0.15, -0.3, 0);
    avatarGroup.add(leftKnee);
    
    const rightKnee = new THREE.Mesh(kneeGeo, jointMaterial);
    rightKnee.position.set(0.15, -0.3, 0);
    avatarGroup.add(rightKnee);
    
    // Lower legs
    const lowerLegGeo = new THREE.CylinderGeometry(0.1, 0.08, 0.6, ...config.lowerLeg);
    
    const leftLowerLeg = new THREE.Mesh(lowerLegGeo, bodyMaterial);
    leftLowerLeg.position.set(-0.15, -0.65, 0);
    if (!isMobile) leftLowerLeg.castShadow = true;
    avatarGroup.add(leftLowerLeg);
    
    const rightLowerLeg = new THREE.Mesh(lowerLegGeo, bodyMaterial);
    rightLowerLeg.position.set(0.15, -0.65, 0);
    if (!isMobile) rightLowerLeg.castShadow = true;
    avatarGroup.add(rightLowerLeg);
    
    // Feet
    const footGeo = new THREE.BoxGeometry(0.15, 0.1, 0.25);
    
    const leftFoot = new THREE.Mesh(footGeo, jointMaterial);
    leftFoot.position.set(-0.15, -0.95, 0.05);
    avatarGroup.add(leftFoot);
    
    const rightFoot = new THREE.Mesh(footGeo, jointMaterial);
    rightFoot.position.set(0.15, -0.95, 0.05);
    avatarGroup.add(rightFoot);
    
    // Store original materials
    avatarGroup.userData.originalMaterials = [];
    avatarGroup.traverse((child) => {
        if (child.isMesh) {
            avatarGroup.userData.originalMaterials.push(child.material);
        }
    });
    
    scene.add(avatarGroup);
}

function createEnvironment() {
    // Ground
    const config = LOD_CONFIG[lodLevel];
    const groundGeo = new THREE.CircleGeometry(4, ...config.ground);
    const groundMat = new THREE.MeshStandardMaterial({
        color: 0x1a1a2e,
        metalness: 0.2,
        roughness: 0.8
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -1.1;
    if (!isMobile) ground.receiveShadow = true;
    scene.add(ground);
    
    // Grid helper - simplified on mobile
    if (!isMobile) {
        const gridHelper = new THREE.GridHelper(8, 20, 0x6366f1, 0x252542);
        gridHelper.position.y = -1.09;
        scene.add(gridHelper);
    }
    
    // Floating particles - fewer on mobile
    if (!isMobile || window.innerWidth > 768) {
        createParticles();
    }
}

function createParticles() {
    const particleGeo = new THREE.BufferGeometry();
    const particleCount = isMobile ? 20 : 50;
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 8;
        positions[i + 1] = Math.random() * 4;
        positions[i + 2] = (Math.random() - 0.5) * 8;
    }
    
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const particleMat = new THREE.PointsMaterial({
        color: 0x6366f1,
        size: 0.05,
        transparent: true,
        opacity: 0.6
    });
    
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);
    
    avatarGroup.userData.particles = particles;
}

function setupControls() {
    const canvas = renderer.domElement;
    
    // Mouse controls
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    
    canvas.addEventListener('mousedown', (e) => {
        isDragging = true;
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    
    canvas.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;
        
        if (avatarGroup) {
            avatarGroup.rotation.y += deltaX * 0.01;
            avatarGroup.rotation.x += deltaY * 0.005;
            avatarGroup.rotation.x = Math.max(-0.5, Math.min(0.5, avatarGroup.rotation.x));
        }
        
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    
    canvas.addEventListener('mouseup', () => isDragging = false);
    canvas.addEventListener('mouseleave', () => isDragging = false);
    
    // Enhanced touch controls with pinch zoom
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', handleTouchEnd, { passive: true });
    canvas.addEventListener('touchcancel', handleTouchEnd, { passive: true });
    
    // Double tap to reset
    canvas.addEventListener('touchend', handleDoubleTap, { passive: true });
    
    // UI Controls
    document.getElementById('resetView')?.addEventListener('click', () => {
        if (avatarGroup) {
            avatarGroup.rotation.set(0, 0, 0);
            camera.position.set(0, 1, 5);
            updateLOD();
            createAvatar();
        }
    });
    
    document.getElementById('toggleRotation')?.addEventListener('click', (e) => {
        isRotating = !isRotating;
        e.currentTarget.classList.toggle('active', isRotating);
    });
    
    document.getElementById('toggleWireframe')?.addEventListener('click', (e) => {
        isWireframe = !isWireframe;
        e.currentTarget.classList.toggle('active', isWireframe);
        
        if (avatarGroup) {
            avatarGroup.traverse((child) => {
                if (child.isMesh) {
                    if (isWireframe) {
                        child.material = new THREE.MeshBasicMaterial({
                            color: 0x6366f1,
                            wireframe: true
                        });
                    } else {
                        child.material = new THREE.MeshStandardMaterial({
                            color: 0x6366f1,
                            metalness: isMobile ? 0.1 : 0.3,
                            roughness: isMobile ? 0.6 : 0.4
                        });
                    }
                }
            });
        }
    });
    
    document.getElementById('zoomIn')?.addEventListener('click', () => {
        camera.position.z = Math.max(2, camera.position.z - 0.5);
        checkLODUpdate();
    });
    
    document.getElementById('zoomOut')?.addEventListener('click', () => {
        camera.position.z = Math.min(8, camera.position.z + 0.5);
        checkLODUpdate();
    });
}

function handleTouchStart(e) {
    touchState.touches = Array.from(e.touches);
    
    if (e.touches.length === 1) {
        touchState.isDragging = true;
        touchState.startX = e.touches[0].clientX;
        touchState.startY = e.touches[0].clientY;
        touchState.lastX = e.touches[0].clientX;
        touchState.lastY = e.touches[0].clientY;
    } else if (e.touches.length === 2) {
        touchState.isPinching = true;
        touchState.isDragging = false;
        touchState.startDistance = getTouchDistance(e.touches);
        touchState.startZoom = camera.position.z;
    }
}

function handleTouchMove(e) {
    if (touchState.isDragging && e.touches.length === 1) {
        e.preventDefault();
        
        const deltaX = e.touches[0].clientX - touchState.lastX;
        const deltaY = e.touches[0].clientY - touchState.lastY;
        
        if (avatarGroup) {
            // More sensitive rotation on mobile
            avatarGroup.rotation.y += deltaX * 0.015;
            avatarGroup.rotation.x += deltaY * 0.008;
            avatarGroup.rotation.x = Math.max(-0.5, Math.min(0.5, avatarGroup.rotation.x));
        }
        
        touchState.lastX = e.touches[0].clientX;
        touchState.lastY = e.touches[0].clientY;
    } else if (touchState.isPinching && e.touches.length === 2) {
        e.preventDefault();
        
        const currentDistance = getTouchDistance(e.touches);
        const scale = touchState.startDistance / currentDistance;
        const newZoom = Math.max(2, Math.min(8, touchState.startZoom * scale));
        
        camera.position.z = newZoom;
        checkLODUpdate();
    }
}

function handleTouchEnd(e) {
    if (e.touches.length === 0) {
        touchState.isDragging = false;
        touchState.isPinching = false;
    } else if (e.touches.length === 1 && touchState.isPinching) {
        // Switch from pinch to drag
        touchState.isPinching = false;
        touchState.isDragging = true;
        touchState.lastX = e.touches[0].clientX;
        touchState.lastY = e.touches[0].clientY;
    }
    
    touchState.touches = Array.from(e.touches);
}

function handleDoubleTap(e) {
    const now = Date.now();
    if (now - touchState.lastTouchTime < 300) {
        // Double tap detected - reset view
        if (avatarGroup) {
            avatarGroup.rotation.set(0, 0, 0);
            camera.position.set(0, 1, 5);
            updateLOD();
            createAvatar();
        }
    }
    touchState.lastTouchTime = now;
}

function getTouchDistance(touches) {
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

function checkLODUpdate() {
    const newLOD = camera.position.z > 6 ? 'low' : camera.position.z > 4 ? 'medium' : 'high';
    if (newLOD !== lodLevel) {
        lodLevel = newLOD;
        createAvatar();
    }
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    
    // Re-detect mobile on resize
    const wasMobile = isMobile;
    isMobile = detectMobile();
    
    if (wasMobile !== isMobile) {
        // Reinitialize with new settings
        init();
    } else {
        updateLOD();
    }
}

function handleVisibilityChange() {
    if (document.hidden) {
        // Pause expensive operations when tab is hidden
        isRotating = false;
    }
}

function lazyLoadResources() {
    // Lazy load comparison feature
    const compareToggle = document.getElementById('compareMode');
    if (compareToggle) {
        compareToggle.addEventListener('change', (e) => {
            if (e.target.checked && !window.comparisonLoaded) {
                loadingManager.show();
                // Simulate loading comparison data
                setTimeout(() => {
                    window.comparisonLoaded = true;
                    loadingManager.hide();
                }, 800);
            }
        });
    }
    
    // Lazy load dashboard data
    const dashboardLinks = document.querySelectorAll('a[href="dashboard.html"]');
    dashboardLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            // Prefetch dashboard on hover
            const prefetch = document.createElement('link');
            prefetch.rel = 'prefetch';
            prefetch.href = 'dashboard.html';
            document.head.appendChild(prefetch);
        }, { once: true });
    });
}

function animate() {
    requestAnimationFrame(animate);
    
    // Skip frames on mobile when tab is hidden
    if (isMobile && document.hidden) return;
    
    if (avatarGroup) {
        // Auto rotation
        if (isRotating) {
            avatarGroup.rotation.y += isMobile ? 0.003 : 0.005;
        }
        
        // Idle animation - simplified on mobile
        if (!isMobile) {
            const time = Date.now() * 0.001;
            avatarGroup.position.y = Math.sin(time) * 0.02;
            
            // Particle animation
            if (avatarGroup.userData.particles) {
                avatarGroup.userData.particles.rotation.y = time * 0.05;
            }
        }
    }
    
    renderer.render(scene, camera);
}

// Export utilities for other modules
window.AvatarUtils = {
    compressImage,
    detectMobile,
    loadingManager
};
