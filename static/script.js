// Theme Management
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const themeToggle = document.getElementById('themeToggle');
        themeToggle.addEventListener('click', () => this.toggle());
    }

    toggle() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.theme);
        localStorage.setItem('theme', this.theme);
    }
}


// Tab Navigation
class TabManager {
    constructor() {
        this.tabs = document.querySelectorAll('.tab-btn');
        this.contents = document.querySelectorAll('.tab-content');
        this.init();
    }

    init() {
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
    }

    switchTab(tabId) {
        // Update tab buttons
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabId);
        });

        // Update tab contents
        this.contents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
    }
}


// User Profile Database (In-Memory Storage)
class ProfileDatabase {
    constructor() {
        this.profile = this.loadProfile();
    }

    loadProfile() {
        const saved = localStorage.getItem('userProfile');
        return saved ? JSON.parse(saved) : null;
    }

    saveProfile(data) {
        this.profile = data;
        localStorage.setItem('userProfile', JSON.stringify(data));
    }

    getProfile() {
        return this.profile;
    }

    clearProfile() {
        this.profile = null;
        localStorage.removeItem('userProfile');
    }

    hasProfile() {
        return this.profile !== null && Object.keys(this.profile).length > 0;
    }
}


// Field Mapping Configuration
const FIELD_MAPPINGS = {
    // Personal Information
    'full_name': ['fullName', 'name', 'applicant_name', 'employee_name'],
    'date_of_birth': ['dateOfBirth', 'birthdate', 'dob'],
    'gender': ['gender', 'sex'],
    'nationality': ['nationality', 'citizenship'],
    
    // Contact Information
    'email': ['email', 'email_address', 'contact_email'],
    'phone': ['phone', 'phone_number', 'contact_number', 'mobile'],
    'alternate_phone': ['alternatePhone', 'alternate_contact', 'secondary_phone'],
    'address': ['address', 'complete_address', 'residential_address', 'home_address'],
    
    // Educational Background
    'education': ['educationLevel', 'highest_education', 'education_level'],
    'school': ['school', 'university', 'institution'],
    'course': ['course', 'program', 'degree', 'major'],
    'year_graduated': ['yearGraduated', 'graduation_year', 'year_of_graduation'],
    
    // Employment Information
    'employer': ['employer', 'company', 'current_employer'],
    'position': ['position', 'job_title', 'designation'],
    'experience': ['experience', 'years_of_experience', 'work_experience'],
    'salary': ['salary', 'monthly_salary', 'income'],
    
    // Government IDs
    'sss_number': ['sssNumber', 'sss', 'social_security'],
    'tin_number': ['tinNumber', 'tin', 'tax_id'],
    'philhealth_number': ['philhealthNumber', 'philhealth', 'health_insurance'],
    'pagibig_number': ['pagibigNumber', 'pagibig', 'hdmf']
};


// Profile Manager
// Profile Manager with Session Support
class ProfileManager {
    constructor() {
        this.form = document.getElementById('profileForm');
        this.init();
    }

    init() {
        // Load session data from server when page loads
        this.loadProfile();

        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfile();
        });

        // Clear button
        document.getElementById('clearProfileBtn').addEventListener('click', () => {
            this.clearForm();
        });
    }

    collectFormData() {
        const data = {};
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.value.trim()) data[input.id] = input.value.trim();
        });
        return data;
    }

    async loadProfile() {
        try {
            const res = await fetch('/get_profile');
            if (!res.ok) return;

            const data = await res.json();
            if (!data.user_data) return;

            Object.keys(data.user_data).forEach(key => {
                const input = document.getElementById(key);
                if (input) input.value = data.user_data[key];
            });
        } catch (err) {
            console.error('Failed to load session profile', err);
        }
    }

    async saveProfile() {
        const data = this.collectFormData();

        // Validate required fields
        const required = ['fullName', 'email', 'phone', 'address'];
        const missing = required.filter(f => !data[f]);
        if (missing.length) {
            alert('Please fill all required fields: ' + missing.join(', '));
            return;
        }

        try {
            const res = await fetch('/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!res.ok) {
                const payload = await res.json().catch(() => ({}));
                alert(payload.error || 'Profile save failed');
                return;
            }

            alert('Profile saved to session!');
        } catch (err) {
            console.error('saveProfile error', err);
            alert('Server error while saving profile');
        }
    }

    async clearForm() {
        // Clear HTML fields
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => input.value = '');

        // Clear server session
        try {
            const res = await fetch('/clear_profile', { method: 'POST' });
            if (res.ok) alert('Profile cleared from session!');
        } catch (err) {
            console.error('Failed to clear session', err);
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new ProfileManager();
});



// Document Upload Manager
class DocumentUploadManager {
    constructor() {
        this.db = new ProfileDatabase();
        this.uploadedFile = null;
        this.detectedFields = [];
        this.init();
    }

    init() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseBtn');
        const removeBtn = document.getElementById('removeFileBtn');
        const processBtn = document.getElementById('processDocumentBtn');

        // Click to upload
        browseBtn.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('click', (e) => {
            if (e.target === uploadArea || e.target.closest('.upload-area')) {
                fileInput.click();
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) this.handleFile(file);
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) this.handleFile(file);
        });

        // Remove file
        removeBtn.addEventListener('click', () => this.removeFile());

        // Process document
        processBtn.addEventListener('click', () => this.processDocument());
    }

    handleFile(file) {
        // Validate file
        const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
        const maxSize = 10 * 1024 * 1024; // 10MB

        if (!validTypes.includes(file.type)) {
            showToast('Please upload a PDF, JPG, or PNG file', 'error');
            return;
        }

        if (file.size > maxSize) {
            showToast('File size must be less than 10MB', 'error');
            return;
        }

        this.uploadedFile = file;
        this.showUploadedFile(file);
    }

    showUploadedFile(file) {
        document.getElementById('uploadArea').style.display = 'none';
        document.getElementById('uploadedFile').style.display = 'block';
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = this.formatFileSize(file.size);
    }

    removeFile() {
        this.uploadedFile = null;
        this.detectedFields = [];
        document.getElementById('uploadArea').style.display = 'block';
        document.getElementById('uploadedFile').style.display = 'none';
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('detectedFields').style.display = 'none';
        document.getElementById('fileInput').value = '';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

async processDocument() {
    if (!this.db.hasProfile()) {
        showToast('Please create your profile first', 'error');
        return;
    }

    if (!this.uploadedFile) {
        showToast('Please upload a document first!', 'error');
        return;
    }

    const statusDiv = document.getElementById('processingStatus');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = `<span>Processing document...</span>`;

    try {
        const res = await fetch("/process", { method: "POST" });
        if (!res.ok) {
            const data = await res.json();
            showToast(data.errors?.join(',') || "Processing failed", "error");
            return;
        }

        // Convert response to blob
        const blob = await res.blob();
        const imgUrl = URL.createObjectURL(blob);

        // Show preview
        document.getElementById('filledDocument').innerHTML = `
            <div style="text-align:center;">
                <img src="${imgUrl}" style="max-width:100%; margin-bottom:1rem"/>
                <br/>
                <button id="downloadFilledFormBtn">Download Filled Form</button>
            </div>
        `;

        // Download functionality
        document.getElementById('downloadFilledFormBtn').addEventListener('click', () => {
            const a = document.createElement('a');
            a.href = imgUrl;
            a.download = 'filled_form.jpg';  // filename for download
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });

        showToast("Document processed successfully!", "success");

    } catch (err) {
        console.error(err);
        showToast("Server error while processing document", "error");
    }
}


    async simulateOCR() {
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Simulate detected fields (in real implementation, this would come from OCR/CFG parsing)
        this.detectedFields = [
            { detected: 'Full Name', mapped: 'fullName' },
            { detected: 'Email Address', mapped: 'email' },
            { detected: 'Phone Number', mapped: 'phone' },
            { detected: 'Address', mapped: 'address' },
            { detected: 'Date of Birth', mapped: 'dateOfBirth' },
            { detected: 'Position', mapped: 'position' },
            { detected: 'Education', mapped: 'educationLevel' }
        ];

        this.showDetectedFields();
    }

    showDetectedFields() {
        const statusDiv = document.getElementById('processingStatus');
        statusDiv.innerHTML = `
            <div class="status-item">
                <div class="status-icon success">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <span>Document analyzed successfully! Found ${this.detectedFields.length} fields.</span>
            </div>
        `;

        const profile = this.db.getProfile();
        const mappingHTML = this.detectedFields.map(field => {
            const value = profile[field.mapped] || 'Not in profile';
            return `
                <div class="mapping-item">
                    <div class="mapping-field">
                        <span class="mapping-label">Detected Field</span>
                        <span class="mapping-value">${field.detected}</span>
                    </div>
                    <svg class="mapping-arrow" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <line x1="5" y1="12" x2="19" y2="12"/>
                        <polyline points="12 5 19 12 12 19"/>
                    </svg>
                    <div class="mapping-field">
                        <span class="mapping-label">Your Data</span>
                        <span class="mapping-value">${value}</span>
                    </div>
                </div>
            `;
        }).join('');

        document.getElementById('detectedFields').style.display = 'block';
        document.getElementById('fieldMapping').innerHTML = mappingHTML;

        // Store for auto-fill tab
        window.currentDocument = {
            file: this.uploadedFile,
            fields: this.detectedFields
        };

        showToast('Document ready for auto-fill! Go to Auto-Fill tab.', 'success');
    }
}


// Auto-Fill Manager
class AutoFillManager {
    constructor() {
        this.db = new ProfileDatabase();
        this.init();
    }

    init() {
        // Check if document is ready when tab is opened
        const autoFillTab = document.querySelector('[data-tab="autofill"]');
        autoFillTab.addEventListener('click', () => {
            this.checkDocumentReady();
        });

        // Export button
        document.getElementById('exportFilledPDF').addEventListener('click', () => {
            this.exportDocument();
        });

        // Edit mapping button
        document.getElementById('editMappingBtn').addEventListener('click', () => {
            const tabManager = new TabManager();
            tabManager.switchTab('upload');
        });
    }

    checkDocumentReady() {
        if (!window.currentDocument) {
            document.getElementById('autofillPlaceholder').style.display = 'flex';
            document.getElementById('autofillPreview').style.display = 'none';
            return;
        }

        document.getElementById('autofillPlaceholder').style.display = 'none';
        document.getElementById('autofillPreview').style.display = 'block';
        this.generateFilledDocument();
    }

    generateFilledDocument() {
        const profile = this.db.getProfile();
        const fields = window.currentDocument.fields;

        const documentHTML = `
            <div style="max-width: 800px; margin: 0 auto;">
                <div style="text-align: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #e5e7eb;">
                    <h1 style="font-size: 2rem; font-weight: 700; color: #1a1a1a; margin-bottom: 0.5rem;">
                        Filled Document
                    </h1>
                    <p style="color: #6c757d;">Auto-filled from your profile</p>
                </div>

                <div style="display: grid; gap: 1.5rem;">
                    ${fields.map(field => {
                        const value = profile[field.mapped] || '[Not Available]';
                        return `
                            <div style="display: grid; grid-template-columns: 200px 1fr; gap: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;">
                                <strong style="color: #1a1a1a;">${field.detected}:</strong>
                                <span style="color: #374151;">${value}</span>
                            </div>
                        `;
                    }).join('')}
                </div>

                <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; text-align: center; color: #6c757d; font-size: 0.875rem;">
                    <p>Generated on ${new Date().toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    })}</p>
                </div>
            </div>
        `;

        document.getElementById('filledDocument').innerHTML = documentHTML;
    }

    exportDocument() {
        const content = document.getElementById('filledDocument');
        const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Filled Document</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            padding: 2rem;
            max-width: 800px;
            margin: 0 auto;
            background: white;
        }
    </style>
</head>
<body>
    ${content.innerHTML}
</body>
</html>
        `;

        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `filled_document_${Date.now()}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast('Document exported successfully!', 'success');
    }
}


// Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    // Set message
    toastMessage.textContent = message;
    
    // Set color based on type
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6',
        warning: '#f59e0b'
    };
    toast.style.backgroundColor = colors[type] || colors.success;
    
    // Show toast
    toast.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}



// Modal Manager
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
}


// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
    new TabManager();
    new ProfileManager();
    new DocumentUploadManager();
    new AutoFillManager();

    document.getElementById('modalCloseBtn')?.addEventListener('click', () => {
        hideModal('profileSavedModal');
    });
    
    document.getElementById('modalClearCloseBtn')?.addEventListener('click', () => {
        hideModal('profileClearedModal');
    });

    // Event listener for Clear Stored Profile Data button
document.getElementById("clearStoredProfileBtn").addEventListener("click", clearStoredProfileData);

});

// Switch to Edit Profile tab
document.querySelector('[data-tab="editProfile"]').addEventListener('click', () => {
    switchTab('editProfile');
    loadProfileForEditing();
});

// Load saved profile data into edit form
function loadProfileForEditing() {
    const savedData = JSON.parse(localStorage.getItem("profileData") || "{}");

    // Loop through saved data and auto-fill matching inputs
    for (const key in savedData) {
        const field = document.querySelector(`#${key}`);
        if (field) field.value = savedData[key];
    }
}

// Re-save edited data
document.getElementById("saveEditedProfileBtn").addEventListener("click", async () => {
    const inputs = document.querySelectorAll("#profileForm input, #profileForm textarea, #profileForm select");
    const updatedData = {};

    inputs.forEach(input => {
        updatedData[input.id] = input.value.trim();
    });

    // Validate required fields
    const required = ["fullName", "email", "phone", "address"];
    const missing = required.filter(f => !updatedData[f]);
    if (missing.length) {
        showToast("Please fill all required fields: " + missing.join(", "), "error");
        return;
    }

    try {
        const res = await fetch("/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updatedData)
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.message || "Profile submission failed", "error");
            return;
        }
        showToast("Profile saved successfully!", "success");
    } catch (err) {
        console.error(err);
        showToast("Server error while submitting profile", "error");
    }
});



// Clear ALL stored profile data (now with the old popup)
function clearStoredProfileData() {
    // Show the old modal BEFORE clearing data
    showModal("profileClearedModal");

    // When the user confirms inside the modal
    const confirmBtn = document.getElementById("confirmClearProfileData");

    confirmBtn.onclick = () => {
        const db = new KC_Database();
        db.clearProfile();

        // Clear fields inside the Edit Data tab
        const editInputs = document.querySelectorAll('#editProfile-tab input, #editProfile-tab textarea, #editProfile-tab select');
        editInputs.forEach(input => input.value = "");

        hideModal("profileClearedModal");
        showToast("Stored profile data deleted!");
    };
}

fileInput.addEventListener("change", async () => {
    const uploadedFile = fileInput.files[0];
    if (!uploadedFile) return;

    const formData = new FormData();
    formData.append("document", uploadedFile); // must match Flask


    try {
        const res = await fetch("/upload", { method: "POST", body: formData });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || "Upload failed", "error");
            return;
        }

        window.currentDocument = { file: data.filename }; // optional for UI
        showToast("File uploaded successfully!", "success");

    } catch (err) {
        console.error(err);
        showToast("Upload failed due to server error", "error");
    }
});


