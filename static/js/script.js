// Custom JavaScript for Frontend Test App

// Global variables
let currentData = null;

// Utility functions
function showLoading(show = true) {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        if (show) {
            loadingElement.classList.remove('d-none');
        } else {
            loadingElement.classList.add('d-none');
        }
    }
}

function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of the main container
    const container = document.querySelector('main.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }
}

// API Functions
async function loadData() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/data');
        const data = await response.json();
        
        if (response.ok) {
            currentData = data;
            displayData(data);
            showAlert('Data loaded successfully!', 'success');
        } else {
            throw new Error(data.message || 'Failed to load data');
        }
    } catch (error) {
        console.error('Error loading data:', error);
        showAlert('Error loading data: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function displayData(data) {
    const container = document.getElementById('data-container');
    if (!container) return;
    
    let html = `
        <div class="fade-in">
            <h5>${data.message}</h5>
            <p><strong>Timestamp:</strong> ${data.timestamp}</p>
            
            <h6>Items:</h6>
            <div class="table-responsive">
                <table class="table table-striped data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    data.items.forEach(item => {
        html += `
            <tr>
                <td>${item.id}</td>
                <td>${item.name}</td>
                <td>${item.description}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

async function submitTestData() {
    const testData = {
        name: 'Test User',
        email: 'test@example.com',
        message: 'This is a test submission',
        timestamp: new Date().toISOString()
    };
    
    try {
        const response = await fetch('/api/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showModal('Success', `<pre>${JSON.stringify(result, null, 2)}</pre>`);
            showAlert('Test data submitted successfully!', 'success');
        } else {
            throw new Error(result.message || 'Failed to submit data');
        }
    } catch (error) {
        console.error('Error submitting data:', error);
        showAlert('Error submitting data: ' + error.message, 'danger');
    }
}

function showModal(title, content) {
    document.querySelector('#resultModal .modal-title').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    
    const modal = new bootstrap.Modal(document.getElementById('resultModal'));
    modal.show();
}

// Form handling
function setupFormHandlers() {
    const testForm = document.getElementById('testForm');
    if (testForm) {
        testForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(testForm);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                message: formData.get('message'),
                timestamp: new Date().toISOString()
            };
            
            try {
                const response = await fetch('/api/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showModal('Form Submitted', `
                        <div class="alert alert-success">
                            Form submitted successfully!
                        </div>
                        <strong>Response:</strong>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    `);
                    testForm.reset();
                } else {
                    throw new Error(result.message || 'Failed to submit form');
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                showAlert('Error submitting form: ' + error.message, 'danger');
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend Test App initialized');
    setupFormHandlers();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.classList.contains('alert-success')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            }
        });
    }, 5000);
});

// Export functions for global access
window.loadData = loadData;
window.submitTestData = submitTestData;