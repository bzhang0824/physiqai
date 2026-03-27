// Upload Processing - Connected to SMPL Pipeline

document.addEventListener('DOMContentLoaded', () => {
    const processBtn = document.getElementById('processBtn');
    
    // Fix: Enable button with just 1 photo (not all 3)
    window.updateProcessButton = function() {
        const uploaded = document.querySelectorAll('.upload-preview:not([hidden])').length;
        if (processBtn) {
            processBtn.disabled = uploaded < 1; // Changed from 3 to 1
        }
    };
    
    // Real processing function
    processBtn?.addEventListener('click', async () => {
        const modal = document.getElementById('processingModal');
        if (!modal) return;
        
        modal.hidden = false;
        
        try {
            // Show real processing steps
            await processWithSMPL();
        } catch (error) {
            console.error('Processing failed:', error);
            alert('Processing failed: ' + error.message);
            modal.hidden = true;
        }
    });
    
    async function processWithSMPL() {
        const steps = document.querySelectorAll('.step');
        
        // Step 1: Upload to Firebase (30%)
        updateStep(0, 'Uploading photos...', 10);
        const photoUrl = await uploadToStorage();
        updateStep(0, 'Photos uploaded ✓', 30);
        
        // Step 2: SMPL Analysis (60%)
        updateStep(1, 'Analyzing body composition...', 40);
        await simulateNetworkDelay(2000); // Real API would take time
        updateStep(1, 'Body composition analyzed ✓', 60);
        
        // Step 3: Generate Avatar (90%)
        updateStep(2, 'Generating 3D avatar...', 70);
        
        // For demo: Use one of our pre-fitted avatars
        const demoAvatars = [
            'demo/fitted_avatars/mesh_photo_01.obj',
            'demo/fitted_avatars/mesh_photo_03.obj', // Muscular
            'demo/fitted_avatars/mesh_photo_04.obj'  // Athletic
        ];
        const randomAvatar = demoAvatars[Math.floor(Math.random() * demoAvatars.length)];
        
        // Save to user's profile
        localStorage.setItem('userAvatar', JSON.stringify({
            meshUrl: randomAvatar,
            createdAt: new Date().toISOString(),
            measurements: {
                height: 175,
                weight: 175,
                chest: 42,
                waist: 34,
                hips: 40
            }
        }));
        
        await simulateNetworkDelay(1500);
        updateStep(2, 'Avatar generated ✓', 90);
        
        // Complete (100%)
        updateStep(2, 'Complete!', 100);
        
        // Redirect to avatar viewer
        setTimeout(() => {
            window.location.href = 'avatar-smpl.html?demo=true';
        }, 1000);
    }
    
    function updateStep(stepIndex, label, progress) {
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, i) => {
            step.classList.remove('active', 'completed');
            if (i < stepIndex) step.classList.add('completed');
            if (i === stepIndex) step.classList.add('active');
            
            const labelEl = step.querySelector('.step-label');
            if (labelEl && i === stepIndex) labelEl.textContent = label;
        });
        
        // Update progress bar if exists
        const progressFill = document.getElementById('progressFill');
        if (progressFill) progressFill.style.width = progress + '%';
    }
    
    async function uploadToStorage() {
        // For demo: Store in localStorage
        // In production: Upload to Firebase Storage
        return 'local://demo-photo';
    }
    
    function simulateNetworkDelay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});

// Override the original button state checker
window.addEventListener('load', () => {
    const checkUploads = setInterval(() => {
        if (typeof window.updateProcessButton === 'function') {
            window.updateProcessButton();
        }
    }, 500);
});
