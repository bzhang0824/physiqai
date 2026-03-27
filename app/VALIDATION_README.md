# PhysiqAI Input Validation System

## Overview
Comprehensive client-side validation module with XSS protection, inline error messages, and form validation orchestration.

## Files
- `validation.js` - Main validation module (550 lines)
- `auth.html` - Demo page showing email validation
- Updated forms: `weight-tracker.html`, `workout-planner.html`, `upload.html`, `dashboard.html`

## Validation Rules

| Field | Type | Range/Format | Error Message |
|-------|------|--------------|---------------|
| Weight | number | 50-500 lbs | "Weight must be between 50 and 500 lbs" |
| Height | number | 48-96 inches | "Height must be between 48 and 96 inches" |
| Age | integer | 13-100 years | "Age must be between 13 and 100 years" |
| Workout Reps | integer | 1-100 | "Reps must be between 1 and 100" |
| Workout Weight | number | 0-2000 lbs | "Weight must be between 0 and 2000 lbs" |
| Goal Weight | number | 50-500 lbs | "Goal weight must be between 50 and 500 lbs" |
| Email | string | Valid email format | "Please enter a valid email address" |
| Date | string | Valid date, not future | "Please enter a valid date (not in the future)" |
| Photo | File | JPG/PNG, <10MB | "Photo must be JPG/PNG and under 10MB" |
| Notes | string | Max 500 chars | "Notes must be under 500 characters" |

## Usage

### 1. Include the validation script
```html
<script src="validation.js"></script>
```

### 2. Add data-validate attributes to inputs
```html
<input type="number" data-validate="weight" name="weight">
<input type="email" data-validate="email" name="email">
<input type="date" data-validate="date" name="date">
```

### 3. Initialize validation on a form
```javascript
// Auto-initialization (forms with data-validate-form attribute)
<form data-validate-form>

// Manual initialization
Validation.initFormValidation('#myForm', {
    onSuccess: (data) => { /* handle valid submission */ },
    onError: (errors) => { /* handle validation errors */ }
});
```

## API Reference

### Individual Validators
```javascript
Validation.validateWeight(value)     // Returns { valid: boolean, message: string }
Validation.validateHeight(value)
Validation.validateAge(value)
Validation.validateReps(value)
Validation.validateWorkoutWeight(value)
Validation.validateEmail(value)
Validation.validateDate(value)
Validation.validatePhoto(file)
Validation.validateNotes(value)
```

### Sanitization (XSS Protection)
```javascript
Validation.sanitizeHTML(input)       // Escapes HTML entities
Validation.sanitizeFormData(form)    // Sanitizes all form inputs
```

### Error Display
```javascript
Validation.showError(input, message)     // Shows red inline error
Validation.clearError(input)             // Clears error styling
Validation.clearAllErrors(form)          // Clears all form errors
```

### Form Validation
```javascript
const result = Validation.validateForm(formElement);
// result: { valid: boolean, data: Object, errors: Array }
```

## Error Styling
Errors appear as red text below inputs with:
- Color: `#ef4444` (red-500)
- Font size: `0.75rem`
- Font weight: `500`
- Input border: changes to red
- ARIA attribute: `aria-invalid="true"`

## XSS Protection
All string inputs are automatically sanitized:
- HTML entities escaped (`<` becomes `&lt;`)
- JavaScript injection prevented
- User content safely displayed

## Examples

### Weight Entry Form
```html
<div class="input-group">
    <label for="weight">Weight</label>
    <input type="number" id="weight" data-validate="weight" name="weight">
</div>
```

### Workout Tracker
```javascript
function logSet() {
    const weightResult = Validation.validateWorkoutWeight(weightInput.value);
    const repsResult = Validation.validateReps(repsInput.value);
    
    if (!weightResult.valid) {
        Validation.showError(weightInput, weightResult.message);
        return;
    }
    // ... proceed with valid data
}
```

### Photo Upload
```javascript
const file = fileInput.files[0];
const result = Validation.validatePhoto(file);

if (!result.valid) {
    showUploadError(result.message);
    return;
}
```

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ JavaScript features
- No external dependencies

## Security Notes
- Client-side validation enhances UX but doesn't replace server-side validation
- Always validate on server before database operations
- XSS sanitization runs automatically on all text inputs
