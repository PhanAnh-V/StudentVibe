// Enhanced form validation for Student Mystery Generator
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionnaire-form');
    const submitBtn = document.getElementById('submit-btn');
    const nameInput = document.querySelector('input[name="name"]');
    
    // Get all textarea elements (6 questions)
    const textareas = document.querySelectorAll('textarea[name^="question"]');
    
    // Disable submit button by default
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '全項目を入力してください';
    }
    
    // Validation function
    function validateForm() {
        if (!nameInput || !submitBtn) return;
        
        // Check if name is filled
        const nameValid = nameInput.value.trim().length > 0;
        
        // Check if all 6 textareas are filled
        let questionsValid = true;
        textareas.forEach(textarea => {
            if (textarea.value.trim().length === 0) {
                questionsValid = false;
            }
        });
        
        // Enable/disable submit button based on validation
        const allValid = nameValid && questionsValid && textareas.length === 6;
        
        if (allValid) {
            submitBtn.disabled = false;
            submitBtn.textContent = '送信';
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-primary');
        } else {
            submitBtn.disabled = true;
            submitBtn.textContent = '全項目を入力してください';
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-secondary');
        }
    }
    
    // Add event listeners to name input
    if (nameInput) {
        nameInput.addEventListener('input', validateForm);
        nameInput.addEventListener('blur', validateForm);
    }
    
    // Add event listeners to all textareas
    textareas.forEach(textarea => {
        textarea.addEventListener('input', validateForm);
        textarea.addEventListener('blur', validateForm);
    });
    
    // Form submission protection
    if (form) {
        form.addEventListener('submit', function(e) {
            // Double-check validation before submission
            const nameValid = nameInput && nameInput.value.trim().length > 0;
            let questionsValid = true;
            
            textareas.forEach(textarea => {
                if (textarea.value.trim().length === 0) {
                    questionsValid = false;
                }
            });
            
            if (!nameValid || !questionsValid || textareas.length !== 6) {
                e.preventDefault();
                alert('すべての項目を入力してください。');
                return false;
            }
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = '送信中...';
            submitBtn.classList.add('btn-warning');
            
            // Allow form submission
            return true;
        });
    }
    
    // Initial validation check
    validateForm();
});

// Auto-resize textareas
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea');
    
    textareas.forEach(textarea => {
        // Set initial height
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(textarea.scrollHeight, 60) + 'px';
        
        // Auto-resize on input
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.max(this.scrollHeight, 60) + 'px';
        });
    });
});