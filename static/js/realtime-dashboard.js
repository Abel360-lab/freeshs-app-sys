/**
 * Real-time Dashboard Updates with WebSockets
 */

class RealtimeDashboard {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/backoffice/dashboard/`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.socket.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus(false, 'Connection lost');
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'dashboard_data':
                this.updateDashboard(data.data);
                break;
            case 'dashboard_updated':
                this.updateDashboard(data.data);
                this.showUpdateNotification();
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateDashboard(data) {
        // Update total applications
        const totalElement = document.querySelector('[data-total-applications]');
        if (totalElement) {
            totalElement.textContent = data.total_applications || 0;
        }
        
        // Update status percentages
        if (data.status_percentages) {
            Object.keys(data.status_percentages).forEach(status => {
                const element = document.querySelector(`[data-percentage="${status.toLowerCase()}"]`);
                if (element) {
                    element.textContent = `${data.status_percentages[status]}%`;
                }
            });
        }
        
        // Update recent applications
        this.updateRecentApplications(data.recent_applications || []);
        
        // Update charts if they exist
        this.updateCharts(data);
    }
    
    updateRecentApplications(applications) {
        const container = document.querySelector('.recent-applications');
        if (!container) return;
        
        const listGroup = container.querySelector('.list-group');
        if (!listGroup) return;
        
        // Clear existing items
        listGroup.innerHTML = '';
        
        applications.forEach(app => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <h6 class="mb-1">${app.business_name}</h6>
                    <small class="text-muted">${app.region_name || 'Unknown Region'}</small>
                </div>
                <span class="badge badge-${app.status.toLowerCase()}">${app.status}</span>
            `;
            listGroup.appendChild(item);
        });
    }
    
    updateCharts(data) {
        // Update ApexCharts if they exist
        if (window.ApexCharts) {
            // Update status distribution chart
            const statusChart = document.querySelector('#statusChart');
            if (statusChart && statusChart._chart) {
                const series = [
                    data.status_percentages.PENDING_REVIEW || 0,
                    data.status_percentages.APPROVED || 0,
                    data.status_percentages.UNDER_REVIEW || 0,
                    data.status_percentages.REJECTED || 0
                ];
                
                statusChart._chart.updateSeries(series);
            }
        }
    }
    
    updateConnectionStatus(connected, message = null) {
        const statusElement = document.querySelector('#connection-status');
        if (statusElement) {
            if (connected) {
                statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> Connected';
                statusElement.className = 'text-success';
            } else {
                statusElement.innerHTML = `<i class="fas fa-circle text-danger"></i> ${message || 'Disconnected'}`;
                statusElement.className = 'text-danger';
            }
        }
    }
    
    showUpdateNotification() {
        // Show a subtle notification that data was updated
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="fas fa-sync-alt"></i> Dashboard updated
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
    
    setupEventListeners() {
        // Refresh data on demand
        const refreshBtn = document.querySelector('#refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.requestDashboardData();
            });
        }
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isConnected) {
                this.requestDashboardData();
            }
        });
    }
    
    requestDashboardData() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'get_dashboard_data'
            }));
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.realtimeDashboard = new RealtimeDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.realtimeDashboard) {
        window.realtimeDashboard.disconnect();
    }
});
