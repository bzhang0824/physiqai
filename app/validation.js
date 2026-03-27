/**
 * PhysiqAI - Input Validation & Sanitization Module
 * Handles all form validation with inline error messages and XSS protection
 */

const Validation = (function() {
    'use strict';

    // Validation Rules Configuration
    const RULES = {
        weight: {
            min: 50,
            max: 500,
            type: 'number',
            message: 'Weight must be between 50 and 500 lbs'
        },
        height: {
            min: 48,
            max: 96,
            type: 'number',
            message: 'Height must be between 48 and 96 inches'
        },
        age: {
            min: 13,
            max: 100,
            type: 'integer',
            message: 'Age must be between 13 and 100 years'
        },
        reps: {
            min: 1,
            max: 100,
            type: 'integer',
            message: 'Reps must be between 1 and 100'
        },
        workoutWeight: {
            min: 0,
            max: 2000,
            type: 'number',
            message: 'Weight must be between 0 and 2000 lbs'
        },
        goalWeight: {
            min: 50,
            max: 500,
            type: 'number',
            message: 'Goal weight must be between 50 and 500 lbs'
        },
        email: {
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            message: 'Please enter a valid email address'
        },
        photo: {
            allowedTypes: ['image/jpeg', 'image/png', 'image/jpg'],
            maxSize: 10 * 1024 * 1024, // 10MB
            message: 'Photo must be JPG/PNG and under 10MB'
        },
        date: {
            message: 'Please enter a valid date (not in the future)'
        },
        notes: {
            maxLength: 500,
            message: 'Notes must be under 500 characters'
        }
    };

    // ============================================
    // SANITIZATION (XSS Protection)
    // ============================================

    /**
     * Sanitize HTML to prevent XSS attacks
     * @param {string} input - Raw input string
     * @returns {string} Sanitized string
     */
    function sanitizeHTML(input) {
        if (typeof input !== 'string') return input;
        
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    /**
     * Sanitize all form inputs
     * @param {HTMLFormElement} form - Form element
     * @returns {Object} Sanitized form data
     */
    function sanitizeFormData(form) {
        const formData = new FormData(form);
        const sanitized = {};
        
        for (const [key, value] of formData.entries()) {
            if (typeof value === 'string') {
                sanitized[key] = sanitizeHTML(value.trim());
            } else {
                sanitized[key] = value;
            }
        }
        
        return sanitized;
    }

    /**
     * Escape special regex characters
     * @param {string} string 
     * @returns {string}
     */
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // ============================================
    // VALIDATION FUNCTIONS
    // ============================================

    /**
     * Validate weight (50-500 lbs)
     * @param {number|string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateWeight(value) {
        const num = parseFloat(value);
        
        if (isNaN(num)) {
            return { valid: false, message: 'Weight must be a valid number' };
        }
        
        if (num < RULES.weight.min || num > RULES.weight.max) {
            return { valid: false, message: RULES.weight.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate height (48-96 inches)
     * @param {number|string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateHeight(value) {
        const num = parseFloat(value);
        
        if (isNaN(num)) {
            return { valid: false, message: 'Height must be a valid number' };
        }
        
        if (num < RULES.height.min || num > RULES.height.max) {
            return { valid: false, message: RULES.height.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate age (13-100, integer)
     * @param {number|string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateAge(value) {
        const num = parseInt(value, 10);
        
        if (isNaN(num) || !Number.isInteger(parseFloat(value))) {
            return { valid: false, message: 'Age must be a whole number' };
        }
        
        if (num < RULES.age.min || num > RULES.age.max) {
            return { valid: false, message: RULES.age.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate workout reps (1-100, integer)
     * @param {number|string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateReps(value) {
        const num = parseInt(value, 10);
        
        if (isNaN(num) || !Number.isInteger(parseFloat(value))) {
            return { valid: false, message: 'Reps must be a whole number' };
        }
        
        if (num < RULES.reps.min || num > RULES.reps.max) {
            return { valid: false, message: RULES.reps.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate workout weight (0-2000 lbs)
     * @param {number|string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateWorkoutWeight(value) {
        const num = parseFloat(value);
        
        if (isNaN(num)) {
            return { valid: false, message: 'Weight must be a valid number' };
        }
        
        if (num < RULES.workoutWeight.min || num > RULES.workoutWeight.max) {
            return { valid: false, message: RULES.workoutWeight.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate email format
     * @param {string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateEmail(value) {
        if (!value || typeof value !== 'string') {
            return { valid: false, message: 'Email is required' };
        }
        
        const trimmed = value.trim();
        
        if (!RULES.email.pattern.test(trimmed)) {
            return { valid: false, message: RULES.email.message };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate date (not in future, valid format)
     * @param {string} value - Date string (YYYY-MM-DD)
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateDate(value) {
        if (!value) {
            return { valid: false, message: 'Date is required' };
        }
        
        const date = new Date(value);
        
        if (isNaN(date.getTime())) {
            return { valid: false, message: 'Please enter a valid date' };
        }
        
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        
        if (date > today) {
            return { valid: false, message: 'Date cannot be in the future' };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate photo file (JPG/PNG, <10MB)
     * @param {File} file 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validatePhoto(file) {
        if (!file) {
            return { valid: false, message: 'Please select a photo' };
        }
        
        if (!RULES.photo.allowedTypes.includes(file.type)) {
            return { valid: false, message: 'Photo must be JPG or PNG format' };
        }
        
        if (file.size > RULES.photo.maxSize) {
            return { valid: false, message: 'Photo must be under 10MB' };
        }
        
        return { valid: true, message: '' };
    }

    /**
     * Validate notes text
     * @param {string} value 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateNotes(value) {
        if (!value) return { valid: true, message: '' };
        
        if (value.length > RULES.notes.maxLength) {
            return { valid: false, message: RULES.notes.message };
        }
        
        return { valid: true, message: '' };
    }

    // ============================================
    // ERROR DISPLAY UTILITIES
    // ============================================

    /**
     * Create or get error element for an input
     * @param {HTMLElement} input 
     * @returns {HTMLElement} Error element
     */
    function getOrCreateErrorElement(input) {
        const parent = input.closest('.input-group') || input.parentElement;
        let errorEl = parent.querySelector('.validation-error');
        
        if (!errorEl) {
            errorEl = document.createElement('span');
            errorEl.className = 'validation-error';
            errorEl.style.cssText = `
                color: #ef4444;
                font-size: 0.75rem;
                margin-top: 4px;
                display: block;
                font-weight: 500;
            `;
            parent.appendChild(errorEl);
        }
        
        return errorEl;
    }

    /**
     * Show error message for an input
     * @param {HTMLElement} input 
     * @param {string} message 
     */
    function showError(input, message) {
        const errorEl = getOrCreateErrorElement(input);
        errorEl.textContent = message;
        input.style.borderColor = '#ef4444';
        input.setAttribute('aria-invalid', 'true');
    }

    /**
     * Clear error message for an input
     * @param {HTMLElement} input 
     */
    function clearError(input) {
        const parent = input.closest('.input-group') || input.parentElement;
        const errorEl = parent.querySelector('.validation-error');
        
        if (errorEl) {
            errorEl.textContent = '';
        }
        
        input.style.borderColor = '';
        input.setAttribute('aria-invalid', 'false');
    }

    /**
     * Clear all errors in a form
     * @param {HTMLFormElement} form 
     */
    function clearAllErrors(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => clearError(input));
    }

    // ============================================
    // FIELD VALIDATION MAPPING
    // ============================================

    /**
     * Validate a single field based on its type
     * @param {HTMLElement} input 
     * @param {string} validationType 
     * @returns {Object} { valid: boolean, message: string }
     */
    function validateField(input, validationType) {
        const value = input.type === 'file' ? input.files[0] : input.value;
        
        switch (validationType) {
            case 'weight':
                return validateWeight(value);
            case 'height':
                return validateHeight(value);
            case 'age':
                return validateAge(value);
            case 'reps':
                return validateReps(value);
            case 'workout-weight':
                return validateWorkoutWeight(value);
            case 'goal-weight':
                return validateWeight(value);
            case 'email':
                return validateEmail(value);
            case 'date':
                return validateDate(value);
            case 'photo':
                return validatePhoto(value);
            case 'notes':
                return validateNotes(value);
            default:
                return { valid: true, message: '' };
        }
    }

    // ============================================
    // FORM VALIDATION
    // ============================================

    /**
     * Validate entire form
     * @param {HTMLFormElement} form 
     * @returns {Object} { valid: boolean, data: Object, errors: Array }
     */
    function validateForm(form) {
        const inputs = form.querySelectorAll('[data-validate]');
        const errors = [];
        let isValid = true;
        const data = {};

        inputs.forEach(input => {
            const validationType = input.dataset.validate;
            const fieldName = input.name || input.id;
            
            // Sanitize value
            let value = input.value;
            if (typeof value === 'string') {
                value = sanitizeHTML(value.trim());
            }
            
            // Validate
            const result = validateField(input, validationType);
            
            if (!result.valid) {
                isValid = false;
                showError(input, result.message);
                errors.push({ field: fieldName, message: result.message });
            } else {
                clearError(input);
                data[fieldName] = value;
            }
        });

        return { valid: isValid, data, errors };
    }

    /**
     * Initialize real-time validation on a form
     * @param {HTMLFormElement|string} form - Form element or selector
     * @param {Object} options 
     */
    function initFormValidation(form, options = {}) {
        const formEl = typeof form === 'string' ? document.querySelector(form) : form;
        
        if (!formEl) {
            console.warn('Form not found for validation:', form);
            return;
        }

        const inputs = formEl.querySelectorAll('[data-validate]');
        
        // Real-time validation on blur
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                const validationType = input.dataset.validate;
                const result = validateField(input, validationType);
                
                if (!result.valid) {
                    showError(input, result.message);
                } else {
                    clearError(input);
                }
            });

            // Clear error on input
            input.addEventListener('input', () => {
                clearError(input);
            });
        });

        // Form submission handler
        formEl.addEventListener('submit', (e) => {
            const result = validateForm(formEl);
            
            if (!result.valid) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus first invalid field
                const firstInvalid = formEl.querySelector('[aria-invalid="true"]');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
                
                if (options.onError) {
                    options.onError(result.errors);
                }
            } else {
                if (options.onSuccess) {
                    e.preventDefault();
                    options.onSuccess(result.data);
                }
            }
        });

        return {
            validate: () => validateForm(formEl),
            clearErrors: () => clearAllErrors(formEl)
        };
    }

    // ============================================
    // PUBLIC API
    // ============================================

    return {
        // Validation functions
        validateWeight,
        validateHeight,
        validateAge,
        validateReps,
        validateWorkoutWeight,
        validateEmail,
        validateDate,
        validatePhoto,
        validateNotes,
        validateField,
        validateForm,
        
        // Sanitization
        sanitizeHTML,
        sanitizeFormData,
        
        // Error handling
        showError,
        clearError,
        clearAllErrors,
        
        // Form initialization
        initFormValidation,
        
        // Configuration
        RULES
    };

})();

// Auto-initialize forms on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Find all forms with validation and initialize them
    const forms = document.querySelectorAll('form[data-validate-form]');
    forms.forEach(form => {
        Validation.initFormValidation(form);
    });
});

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Validation;
}
