// Dark mode functionality
(() => {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Check for saved theme preference or use the system preference
    const currentTheme = localStorage.getItem('theme') || 
                        (prefersDarkScheme.matches ? 'dark' : 'light');
    
    // Apply the theme
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.innerHTML = '<i class="fas fa-sun" aria-hidden="true"></i>';
    }
    
    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        
        // Update button icon
        const isDark = document.body.classList.contains('dark-theme');
        themeToggle.innerHTML = isDark ? 
            '<i class="fas fa-sun" aria-hidden="true"></i>' : 
            '<i class="fas fa-moon" aria-hidden="true"></i>';
        
        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
})();

// Main application code
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the dashboard
    initDashboard();
});

const initDashboard = () => {
    // Set up event listeners
    setupEventListeners();
    
    // Initial data fetch with slight delay to show loading animation
    setTimeout(() => {
        fetchVMs();
    }, 800);
};

const setupEventListeners = () => {
    // Search functionality
    const searchInput = document.getElementById('vm-search');
    searchInput.addEventListener('input', debounce(filterVMs, 300));

    // Refresh button
    const refreshButton = document.getElementById('refresh-button');
    refreshButton.addEventListener('click', () => {
        // Clear the search input
        searchInput.value = '';
        
        // Show loading state on button
        const buttonText = refreshButton.innerHTML;
        refreshButton.innerHTML = `<span class="btn-text">${buttonText}</span>`;
        refreshButton.classList.add('loading');
        
        // Fetch fresh VM data
        fetchVMs().finally(() => {
            // Remove loading state when done
            setTimeout(() => {
                refreshButton.innerHTML = buttonText;
                refreshButton.classList.remove('loading');
            }, 300);
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + R to refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshButton.click();
        }
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            searchInput.focus();
        }
    });
};

// Debounce function to limit how often a function can be called
const debounce = (func, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(null, args);
        }, delay);
    };
};

const filterVMs = () => {
    const searchTerm = document.getElementById('vm-search').value.toLowerCase();
    const rows = document.querySelectorAll('#vm-table tbody tr');
    let hasVisibleRows = false;
    
    rows.forEach(row => {
        if (row.id === 'no-results-row') return; // Skip the no results row
        const vmName = row.querySelector('td:first-child').textContent.toLowerCase();
        if (vmName.includes(searchTerm)) {
            row.style.display = '';
            hasVisibleRows = true;
        } else {
            row.style.display = 'none';
        }
    });

    // Show "No results" message if no VMs match the search
    const noResultsRow = document.querySelector('#no-results-row');
    if (!hasVisibleRows && searchTerm) {
        if (!noResultsRow) {
            const row = document.createElement('tr');
            row.id = 'no-results-row';
            row.innerHTML = `
                <td colspan="7" style="text-align: center; color: var(--text-muted);">
                    <i class="fas fa-search" aria-hidden="true"></i> No VMs found matching "${searchTerm}"
                </td>
            `;
            document.querySelector('#vm-table tbody').appendChild(row);
        }
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
};

// Fetch with retry functionality
const fetchWithRetry = async (url, options = {}, retries = 2, delay = 1000) => {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            
            // Return successful responses or authentication errors (don't retry auth errors)
            if (response.ok || response.status === 401) {
                return response;
            }
            
            // For other errors, throw to trigger retry
            throw new Error(`HTTP error! Status: ${response.status}`);
            
        } catch (error) {
            // If this is the last attempt, throw the error
            if (attempt === retries) {
                throw error;
            }
            
            // Wait before retrying
            console.log(`Retrying fetch to ${url}, ${retries - attempt} attempts left`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

const fetchVMs = async () => {
    const tableBody = document.querySelector('#vm-table tbody');
    
    // Clear any error messages
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
    
    // Show skeleton loading state
    tableBody.innerHTML = '';
    
    // Create 5 skeleton rows for better UX during loading
    for (let i = 0; i < 5; i++) {
        const skeletonRow = document.createElement('tr');
        skeletonRow.className = 'skeleton-row';
        skeletonRow.innerHTML = `
            <td data-label="Name">
                <div class="skeleton skeleton-text medium"></div>
            </td>
            <td data-label="Cluster">
                <div class="skeleton skeleton-text short"></div>
            </td>
            <td data-label="Status">
                <div class="skeleton skeleton-text short"></div>
            </td>
            <td data-label="vCPUs">
                <div class="skeleton skeleton-text short"></div>
            </td>
            <td data-label="Memory">
                <div class="skeleton skeleton-text short"></div>
            </td>
            <td data-label="IP Addresses">
                <div class="skeleton skeleton-text"></div>
            </td>
            <td data-label="Actions">
                <div class="skeleton skeleton-button"></div>
            </td>
        `;
        tableBody.appendChild(skeletonRow);
    }
    
    try {
        // Small delay to ensure DOM is updated
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Use fetch with retry instead of regular fetch
        const response = await fetchWithRetry('/api/vms', {}, 2, 1000);
        
        if (!response.ok) {
            if (response.status === 401) {
                // Handle authentication error
                try {
                    const errorData = await response.json();
                    // Show a user-friendly message before redirecting
                    showToast({
                        title: 'Session Expired',
                        message: 'Your session has expired. Redirecting to login...',
                        type: 'warning',
                        duration: 2000
                    });
                    
                    // Redirect after a short delay
                    setTimeout(() => {
                        if (errorData.redirect) {
                            window.location.href = errorData.redirect;
                        } else {
                            window.location.href = '/login';
                        }
                    }, 2000);
                    return;
                } catch (e) {
                    // If we can't parse the JSON, just redirect to login
                    window.location.href = '/login';
                    return;
                }
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Failed to parse JSON response:', jsonError);
            throw new Error('Invalid response from server. Please refresh the page and try again.');
        }
        
        // Clear loading message
        tableBody.innerHTML = ''; 
        
        if (data.length === 0) {
            showMessage('No powered on VMs found.', 'warning');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="7" style="text-align: center;">
                    No virtual machines are currently powered on.
                </td>
            `;
            tableBody.appendChild(row);
        } else {
            // Render each VM row
            data.forEach(vm => {
                renderVMRow(vm, tableBody);
            });
        }
        
        // Update last updated timestamp
        updateTimestamp();
        
        // Show success toast
        showToast({
            title: 'Data Refreshed',
            message: `Successfully loaded ${data.length} virtual machines.`,
            type: 'success',
            duration: 3000
        });
        
    } catch (error) {
        console.error('Error fetching VM data:', error);
        
        // More detailed error message
        const errorMessage = error.message || 'Unknown error';
        showMessage(`Error loading VM data: ${errorMessage}. Please try again later.`, 'error');
        
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--nutanix-danger);">
                    <i class="fas fa-exclamation-triangle" aria-hidden="true"></i> 
                    Unable to load VM data: ${errorMessage}
                </td>
            </tr>
        `;
        
        // Log additional diagnostic information
        console.log('Navigator online status:', navigator.onLine);
        console.log('Document readyState:', document.readyState);
    }
};

const renderVMRow = (vm, tableBody) => {
    const row = document.createElement('tr');
    row.setAttribute('data-vm-id', vm.id || '');
    
    // Add data-label attributes for responsive tables
    row.innerHTML = `
        <td data-label="Name"><strong>${escapeHTML(vm.name)}</strong></td>
        <td data-label="Cluster">${escapeHTML(vm.cluster_name)}</td>
        <td data-label="Status">
            <span class="status status-active">
                <i class="fas fa-circle" aria-hidden="true"></i>
                <span>&nbsp;Running</span>
            </span>
        </td>
        <td data-label="vCPUs">${vm.vcpus}</td>
        <td data-label="Memory">${vm.memory_gb} GB</td>
        <td data-label="IP Addresses">${vm.ip_addresses ? escapeHTML(vm.ip_addresses.join(', ')) : 'No IP'}</td>
        <td data-label="Actions">
            <a href="${escapeHTML(vm.console_url)}" 
               class="btn btn-primary console-btn" 
               target="_blank"
               rel="noopener"
               aria-label="Open console for ${escapeHTML(vm.name)}"
               title="Open console in new tab: ${escapeHTML(vm.console_url)}">
                <i class="fas fa-terminal btn-icon" aria-hidden="true"></i> Console
            </a>
        </td>
    `;
    
    tableBody.appendChild(row);
};

// Helper function to prevent XSS
const escapeHTML = (str) => {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
};

const updateTimestamp = () => {
    const now = new Date();
    const options = { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: true
    };
    document.getElementById('last-updated-time').textContent = 
        now.toLocaleTimeString(undefined, options);
};

const showMessage = (message, type = 'error') => {
    // For backward compatibility, still update the error element
    if (type === 'error') {
        const errorElement = document.getElementById('error-message');
        errorElement.style.display = 'flex';
        errorElement.querySelector('.alert-text').textContent = message;
    }
    
    // Also show a toast notification
    showToast({
        title: type === 'error' ? 'Error' : 
               type === 'warning' ? 'Warning' : 
               type === 'success' ? 'Success' : 'Information',
        message: message,
        type: type
    });
};

// Toast notification system
const showToast = ({ title, message, type = 'info', duration = 5000 }) => {
    const container = document.getElementById('toast-container');
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    
    // Set icon based on type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon} toast-icon" aria-hidden="true"></i>
        <div class="toast-content">
            <div class="toast-title">${escapeHTML(title)}</div>
            <div class="toast-message">${escapeHTML(message)}</div>
        </div>
        <button class="toast-close" aria-label="Close notification">
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Set up close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        removeToast(toast);
    });
    
    // Auto-remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);
    
    return toast;
};

const removeToast = (toast) => {
    if (!toast || toast.classList.contains('hiding')) return;
    
    toast.classList.add('hiding');
    toast.addEventListener('animationend', () => {
        toast.remove();
    });
};