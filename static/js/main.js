// Main JavaScript file for the Loan Insights Platform

// Global variables
let currentChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    setupFormValidation();
    setupNavigationHighlight();
    
    // Initialize specific page functionality
    if (window.location.pathname === '/apply') {
        initializeApplyPage();
    }
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Setup form validation
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Highlight current navigation item
function setupNavigationHighlight() {
    const currentLocation = location.pathname;
    const menuItems = document.querySelectorAll('.navbar-nav .nav-link');
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentLocation) {
            item.classList.add('active');
        }
    });
}

// Initialize apply page specific functionality
function initializeApplyPage() {
    // Format SSN input
    const ssnInput = document.getElementById('ssn');
    if (ssnInput) {
        ssnInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 3) {
                value = value.substring(0, 3) + '-' + value.substring(3);
            }
            if (value.length >= 6) {
                value = value.substring(0, 6) + '-' + value.substring(6, 10);
            }
            e.target.value = value;
        });
    }

    // Format phone input
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 3) {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3);
            }
            if (value.length >= 9) {
                value = value.substring(0, 9) + '-' + value.substring(9, 13);
            }
            e.target.value = value;
        });
    }

    // Auto-calculate DTI
    const annualIncomeInput = document.getElementById('annualIncome');
    const monthlyDebtInput = document.getElementById('monthlyDebt');
    
    if (annualIncomeInput && monthlyDebtInput) {
        annualIncomeInput.addEventListener('input', calculateDTI);
        monthlyDebtInput.addEventListener('input', calculateDTI);
    }
}

// Calculate DTI ratio
function calculateDTI() {
    const annualIncome = parseFloat(document.getElementById('annualIncome').value) || 0;
    const monthlyDebt = parseFloat(document.getElementById('monthlyDebt').value) || 0;
    
    if (annualIncome > 0) {
        const monthlyIncome = annualIncome / 12;
        const dti = monthlyDebt / monthlyIncome;
        
        // Show DTI ratio as guidance
        const existingDTI = document.getElementById('dti-display');
        if (existingDTI) {
            existingDTI.remove();
        }
        
        if (dti > 0) {
            const dtiDisplay = document.createElement('div');
            dtiDisplay.id = 'dti-display';
            dtiDisplay.className = 'form-text mt-2';
            dtiDisplay.innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-calculator"></i> Current DTI Ratio: ${(dti * 100).toFixed(1)}%
                    ${dti > 0.43 ? '<span class="text-danger">(High DTI may affect approval)</span>' : 
                      dti > 0.36 ? '<span class="text-warning">(Moderate DTI)</span>' : 
                      '<span class="text-success">(Good DTI)</span>'}
                </small>
            `;
            document.getElementById('monthlyDebt').parentNode.appendChild(dtiDisplay);
        }
    }
}

// Submit loan application
async function submitLoanApplication(formData) {
    try {
        const response = await fetch('/api/applications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            return { success: true, application: result.application };
        } else {
            return { success: false, error: result.error || 'Unknown error occurred' };
        }
    } catch (error) {
        console.error('Error submitting application:', error);
        return { success: false, error: 'Network error occurred' };
    }
}

// Helper functions for risk assessment
function getRiskLevel(score) {
    if (score >= 0.8) return 'Low Risk';
    if (score >= 0.6) return 'Medium Risk';
    if (score >= 0.4) return 'High Risk';
    return 'Very High Risk';
}

function getRiskBadgeColor(score) {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    if (score >= 0.4) return 'danger';
    return 'dark';
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Utility function to format percentage
function formatPercentage(value) {
    return (value * 100).toFixed(1) + '%';
}

// Show loading spinner
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
}

// Hide loading spinner
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Refresh dashboard applications (for employee dashboard)
async function refreshDashboardApplications() {
    try {
        const response = await fetch('/api/applications');
        const applications = await response.json();
        
        if (response.ok) {
            updateDashboardTable(applications);
            updateDashboardStats(applications);
        } else {
            console.error('Failed to refresh applications');
        }
    } catch (error) {
        console.error('Error refreshing applications:', error);
    }
}

// Update dashboard table
function updateDashboardTable(applications) {
    const tableBody = document.querySelector('#applicationsTable tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    applications.forEach(app => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${app.id}</td>
            <td>${app.applicant}</td>
            <td>${formatCurrency(app.amount)}</td>
            <td>${formatPercentage(app.riskScore)}</td>
            <td><span class="badge bg-${getStatusColor(app.status)}">${app.status}</span></td>
            <td>${app.date}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewApplication('${app.id}')">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="approveApplication('${app.id}')">
                    <i class="fas fa-check"></i> Approve
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="rejectApplication('${app.id}')">
                    <i class="fas fa-times"></i> Reject
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Update dashboard stats
function updateDashboardStats(applications) {
    const pending = applications.filter(app => app.status === 'Pending').length;
    const approved = applications.filter(app => app.status === 'Approved').length;
    const approvalRate = applications.length > 0 ? (approved / applications.length * 100).toFixed(1) : 0;
    const totalDisbursed = applications
        .filter(app => app.status === 'Approved')
        .reduce((sum, app) => sum + app.amount, 0);
    
    // Update stat cards
    const pendingElement = document.getElementById('pending-count');
    const approvedElement = document.getElementById('approved-count');
    const approvalRateElement = document.getElementById('approval-rate');
    const totalDisbursedElement = document.getElementById('total-disbursed');
    
    if (pendingElement) pendingElement.textContent = pending;
    if (approvedElement) approvedElement.textContent = approved;
    if (approvalRateElement) approvalRateElement.textContent = approvalRate + '%';
    if (totalDisbursedElement) totalDisbursedElement.textContent = formatCurrency(totalDisbursed);
}

// Get status color for badges
function getStatusColor(status) {
    switch (status) {
        case 'Approved': return 'success';
        case 'Rejected': return 'danger';
        case 'Pending': return 'warning';
        case 'Under Review': return 'info';
        default: return 'secondary';
    }
}

// Application action functions for employee dashboard
async function approveApplication(appId) {
    if (confirm('Are you sure you want to approve this application?')) {
        await updateApplicationStatus(appId, 'Approved');
    }
}

async function rejectApplication(appId) {
    if (confirm('Are you sure you want to reject this application?')) {
        await updateApplicationStatus(appId, 'Rejected');
    }
}

async function updateApplicationStatus(appId, status) {
    try {
        const response = await fetch(`/api/applications/${appId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: status })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`Application ${status.toLowerCase()} successfully!`, 'success');
            refreshDashboardApplications();
        } else {
            showNotification(`Error: ${result.error}`, 'danger');
        }
    } catch (error) {
        showNotification('Network error occurred', 'danger');
    }
}

// View application details
function viewApplication(appId) {
    // This would open a modal or navigate to a detail page
    console.log('View application:', appId);
    // For now, just show an alert
    alert(`Viewing application ${appId}`);
}

// Export functions to global scope
window.submitLoanApplication = submitLoanApplication;
window.refreshDashboardApplications = refreshDashboardApplications;
window.approveApplication = approveApplication;
window.rejectApplication = rejectApplication;
window.viewApplication = viewApplication;