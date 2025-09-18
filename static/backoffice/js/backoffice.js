/**
 * Backoffice Common JavaScript Functions
 */

// Global variables
let sidebarCollapsed = false;
let searchTimeout = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeBackoffice();
});

/**
 * Initialize backoffice functionality
 */
function initializeBackoffice() {
    initializeSidebar();
    initializeTooltips();
    initializeSearch();
    initializeModals();
    initializeTables();
    initializeCharts();
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.backoffice-main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
}

/**
 * Initialize sidebar functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.backoffice-sidebar');
    const mainContent = document.querySelector('.backoffice-main');
    
    if (sidebarToggle && sidebar && mainContent) {
        // Add no-transition class to prevent any animations during initialization
        sidebar.classList.add('no-transition');
        mainContent.classList.add('no-transition');
        
        // Check localStorage for sidebar state
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebarCollapsed = true;
        }
        
        // Apply the correct state immediately
        if (sidebarCollapsed) {
            // Apply collapsed state to both sidebar and main content simultaneously
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
        } else {
            // Apply expanded state to both sidebar and main content simultaneously
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        }
        
        // Make sidebar visible and remove no-transition class
        requestAnimationFrame(() => {
            sidebar.classList.add('initialized');
            mainContent.classList.add('initialized');
            sidebar.classList.remove('no-transition');
            mainContent.classList.remove('no-transition');
        });
        
        sidebarToggle.addEventListener('click', function() {
            toggleSidebar();
        });
    }
}

/**
 * Toggle sidebar collapse state
 */
function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
    
    const sidebar = document.querySelector('.backoffice-sidebar');
    const mainContent = document.querySelector('.backoffice-main');
    
    if (sidebar && mainContent) {
        // Enable transitions only for manual toggle
        sidebar.style.transition = 'var(--transition)';
        mainContent.style.transition = 'var(--transition)';
        
        if (sidebarCollapsed) {
            // Apply collapsed state to both elements simultaneously
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
        } else {
            // Apply expanded state to both elements simultaneously
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        }
        
        // Disable transitions after animation completes
        setTimeout(() => {
            sidebar.style.transition = 'none';
            mainContent.style.transition = 'none';
        }, 300); // Match the transition duration
    }
    
    // Save state to localStorage
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
}

/**
 * Collapse sidebar
 */
function collapseSidebar() {
    const sidebar = document.querySelector('.backoffice-sidebar');
    const mainContent = document.querySelector('.backoffice-main');
    
    if (sidebar && mainContent) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }
}

/**
 * Expand sidebar
 */
function expandSidebar() {
    const sidebar = document.querySelector('.backoffice-sidebar');
    const mainContent = document.querySelector('.backoffice-main');
    
    if (sidebar && mainContent) {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('sidebar-collapsed');
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this);
            }, 500); // 500ms delay
        });
    });
}

/**
 * Perform search operation
 */
function performSearch(input) {
    const form = input.closest('form');
    if (form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value && value.trim() !== '' && value !== 'None') {
                params.append(key, value);
            }
        }
        
        const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
        window.location.href = newUrl;
    }
}

/**
 * Initialize modal functionality
 */
function initializeModals() {
    // Handle modal confirmations
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize table functionality
 */
function initializeTables() {
    // Add hover effects to table rows
    document.querySelectorAll('.table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(0, 123, 255, 0.05)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Initialize sortable tables
    initializeSortableTables();
}

/**
 * Initialize sortable tables
 */
function initializeSortableTables() {
    document.querySelectorAll('.sortable-table th[data-sort]').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add sort class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();
        
        if (isAscending) {
            return bText.localeCompare(aText);
        } else {
            return aText.localeCompare(bText);
        }
    });
    
    // Reorder rows in table
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Check if ApexCharts is available
    if (typeof ApexCharts !== 'undefined') {
        initializeDashboardCharts();
    }
}

/**
 * Initialize dashboard charts
 */
function initializeDashboardCharts() {
    // Status distribution chart
    const statusChartElement = document.getElementById('statusChart');
    if (statusChartElement) {
        const statusOptions = {
            series: [
                parseInt(statusChartElement.dataset.pendingReview) || 0,
                parseInt(statusChartElement.dataset.approved) || 0,
                parseInt(statusChartElement.dataset.underReview) || 0,
                parseInt(statusChartElement.dataset.rejected) || 0
            ],
            chart: {
                type: 'donut',
                height: 250
            },
            labels: ['Pending Review', 'Approved', 'Under Review', 'Rejected'],
            colors: ['#ffc107', '#28a745', '#17a2b8', '#dc3545'],
            dataLabels: {
                enabled: false
            },
            plotOptions: {
                pie: {
                    donut: {
                        size: '70%',
                        labels: {
                            show: true,
                            total: {
                                show: true,
                                label: 'Total',
                                formatter: function (w) {
                                    return '100.0%';
                                }
                            }
                        }
                    }
                }
            },
            legend: {
                show: false
            }
        };
        
        const statusChart = new ApexCharts(statusChartElement, statusOptions);
        statusChart.render();
    }
}

/**
 * Initialize application management functionality
 */
function initializeApplicationManagement() {
    // Check if we're on the applications page
    if (window.location.pathname.includes('/backoffice/applications/')) {
        initializeApplicationFilters();
        initializeApplicationActions();
    }
}

/**
 * Initialize application filters
 */
function initializeApplicationFilters() {
    const searchInput = document.getElementById('search');
    const statusSelect = document.getElementById('status');
    const regionSelect = document.getElementById('region');
    const clearButton = document.getElementById('clearFilters');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            performSearch();
        }, 500));
    }
    
    if (statusSelect) {
        statusSelect.addEventListener('change', performSearch);
    }
    
    if (regionSelect) {
        regionSelect.addEventListener('change', performSearch);
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (statusSelect) statusSelect.value = '';
            if (regionSelect) regionSelect.value = '';
            performSearch();
        });
    }
}

/**
 * Perform search operation for applications
 */
function performSearch() {
    const form = document.getElementById('searchForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    for (let [key, value] of formData.entries()) {
        if (value && value.trim() !== '' && value !== 'None') {
            params.append(key, value);
        }
    }
    
    const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    window.location.href = newUrl;
}

/**
 * Initialize application actions
 */
function initializeApplicationActions() {
    // Initialize action buttons
    initializeActionButtons();
    
    // Initialize modals
    initializeApplicationModals();
}

/**
 * Initialize action buttons
 */
function initializeActionButtons() {
    // Approve button
    const approveBtn = document.querySelector('[onclick*="showApproveModal"]');
    if (approveBtn) {
        approveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showApproveModal();
        });
    }
    
    // Reject button
    const rejectBtn = document.querySelector('[onclick*="showRejectModal"]');
    if (rejectBtn) {
        rejectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showRejectModal();
        });
    }
    
    // Request documents button
    const requestDocsBtn = document.querySelector('[onclick*="showRequestDocumentsModal"]');
    if (requestDocsBtn) {
        requestDocsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showRequestDocumentsModal();
        });
    }
}

/**
 * Initialize application modals
 */
function initializeApplicationModals() {
    // Initialize approve modal
    const approveModal = document.getElementById('approveModal');
    if (approveModal) {
        const form = approveModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                submitApproval();
            });
        }
    }
    
    // Initialize reject modal
    const rejectModal = document.getElementById('rejectModal');
    if (rejectModal) {
        const form = rejectModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                submitRejection();
            });
        }
    }
    
    // Initialize request documents modal
    const requestDocsModal = document.getElementById('requestDocumentsModal');
    if (requestDocsModal) {
        const form = requestDocsModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                submitDocumentRequest();
            });
        }
    }
}

/**
 * Show approve modal
 */
function showApproveModal() {
    const modal = document.getElementById('approveModal');
    if (modal && typeof bootstrap !== 'undefined') {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

/**
 * Show reject modal
 */
function showRejectModal() {
    const modal = document.getElementById('rejectModal');
    if (modal && typeof bootstrap !== 'undefined') {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

/**
 * Show request documents modal
 */
function showRequestDocumentsModal() {
    const modal = document.getElementById('requestDocumentsModal');
    if (modal && typeof bootstrap !== 'undefined') {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

/**
 * Submit approval
 */
function submitApproval() {
    const form = document.getElementById('approveModal').querySelector('form');
    const formData = new FormData(form);
    const url = form.action;
    
    showLoading(form);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Application approved successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.error || 'Failed to approve application', 'danger');
        }
    })
    .catch(error => {
        console.error('Approval failed:', error);
        showNotification('Failed to approve application', 'danger');
    })
    .finally(() => {
        hideLoading(form);
    });
}

/**
 * Submit rejection
 */
function submitRejection() {
    const form = document.getElementById('rejectModal').querySelector('form');
    const formData = new FormData(form);
    const url = form.action;
    
    showLoading(form);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Application rejected successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.error || 'Failed to reject application', 'danger');
        }
    })
    .catch(error => {
        console.error('Rejection failed:', error);
        showNotification('Failed to reject application', 'danger');
    })
    .finally(() => {
        hideLoading(form);
    });
}

/**
 * Submit document request
 */
function submitDocumentRequest() {
    const form = document.getElementById('requestDocumentsModal').querySelector('form');
    const formData = new FormData(form);
    const url = form.action;
    
    showLoading(form);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Document request sent successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.error || 'Failed to send document request', 'danger');
        }
    })
    .catch(error => {
        console.error('Document request failed:', error);
        showNotification('Failed to send document request', 'danger');
    })
    .finally(() => {
        hideLoading(form);
    });
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility function to show loading state
 */
function showLoading(element) {
    element.classList.add('loading');
    element.style.pointerEvents = 'none';
}

/**
 * Utility function to hide loading state
 */
function hideLoading(element) {
    element.classList.remove('loading');
    element.style.pointerEvents = '';
}

/**
 * Utility function to show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}
