// Boleto Extractor Web Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('filePreview');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const fileInputWrapper = document.querySelector('.file-input-wrapper');

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop handlers
    fileInputWrapper.addEventListener('dragover', function(e) {
        e.preventDefault();
        fileInputWrapper.classList.add('dragover');
    });

    fileInputWrapper.addEventListener('dragleave', function(e) {
        e.preventDefault();
        fileInputWrapper.classList.remove('dragover');
    });

    fileInputWrapper.addEventListener('drop', function(e) {
        e.preventDefault();
        fileInputWrapper.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type === 'application/pdf') {
                fileInput.files = files;
                handleFileSelect(file);
            } else {
                showToast('Please select a PDF file', 'error');
            }
        }
    });

    // Form submission handler
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showToast('Please select a PDF file', 'error');
            return;
        }

        // Validate file size (16MB max)
        const file = fileInput.files[0];
        if (file.size > 16 * 1024 * 1024) {
            showToast('File too large. Maximum size is 16MB.', 'error');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.querySelector('span').textContent = 'Processing...';
        loadingSpinner.classList.add('show');

        // Submit form
        this.submit();
    });

    // Copy to clipboard functionality
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('Copied to clipboard!', 'success');
            }).catch(function(err) {
                console.error('Failed to copy: ', err);
                fallbackCopyToClipboard(text);
            });
        } else {
            fallbackCopyToClipboard(text);
        }
    };

    // Fallback copy function for older browsers
    function fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showToast('Copied to clipboard!', 'success');
            } else {
                showToast('Failed to copy to clipboard', 'error');
            }
        } catch (err) {
            console.error('Fallback: Oops, unable to copy', err);
            showToast('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    }

    // Handle file selection
    function handleFileSelect(file) {
        if (!file) return;

        if (file.type !== 'application/pdf') {
            showToast('Please select a PDF file', 'error');
            fileInput.value = '';
            return;
        }

        // Update file preview
        filePreview.innerHTML = `
            <i class="fas fa-file-pdf"></i>
            <strong>${file.name}</strong>
            <span>(${formatFileSize(file.size)})</span>
        `;
        filePreview.classList.add('show');

        // Update file input wrapper text
        const fileText = filePreview.querySelector('.file-text');
        if (fileText) {
            fileText.textContent = file.name;
        }
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Show toast notification
    function showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());

        // Create new toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            ${message}
        `;

        // Add to page
        document.body.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease-out reverse';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // API testing functionality (for development)
    window.testAPI = function() {
        const testFile = fileInput.files[0];
        if (!testFile) {
            showToast('Please select a file first', 'error');
            return;
        }

        // Convert file to base64
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64 = e.target.result.split(',')[1];
            
            const requestData = {
                file: base64,
                password: document.getElementById('password').value,
                format: document.getElementById('format').checked
            };

            fetch('/api/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`API Success: Found ${data.count} boleto(s)`, 'success');
                    console.log('API Response:', data);
                } else {
                    showToast(`API Error: ${data.error}`, 'error');
                    console.error('API Error:', data);
                }
            })
            .catch(error => {
                showToast(`API Error: ${error.message}`, 'error');
                console.error('API Error:', error);
            });
        };
        
        reader.readAsDataURL(testFile);
    };

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        }, 5000);
    });

    // Form validation
    const passwordInput = document.getElementById('password');
    const formatCheckbox = document.getElementById('format');

    // Real-time validation
    fileInput.addEventListener('change', validateForm);
    passwordInput.addEventListener('input', validateForm);
    formatCheckbox.addEventListener('change', validateForm);

    function validateForm() {
        const hasFile = fileInput.files.length > 0;
        const isValidFile = hasFile && fileInput.files[0].type === 'application/pdf';
        
        if (isValidFile) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }

    // Initial form validation
    validateForm();
});

// Utility functions for external use
window.BoletoExtractor = {
    copyToClipboard: window.copyToClipboard,
    testAPI: window.testAPI
};
