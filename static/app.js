// Legal Cases Dashboard JavaScript
class LegalCasesDashboard {
    constructor() {
        this.apiBaseUrl = '';
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.currentFilters = {};
        this.cases = [];
        this.editingCaseId = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkApiConnection();
        await this.loadFilterOptions();
        await this.loadCases();
        this.updateStats();
    }

    setupEventListeners() {
        // Search and filter events
        $('#searchBtn').click(() => this.performSearch());
        $('#clearFilters').click(() => this.clearAllFilters());
        $('#searchInput').keypress((e) => {
            if (e.which === 13) this.performSearch();
        });

        // Filter change events
        $('#caseTypeFilter, #statusFilter, #countyFilter, #dateFrom, #dateTo').change(() => {
            this.performSearch();
        });

        // Case management events
        $('#addCaseBtn').click(() => this.showAddCaseModal());
        $('#saveCaseBtn').click(() => this.saveCase());
        $('#editCaseBtn').click(() => this.editCurrentCase());
        $('#exportBtn').click(() => this.exportCases());

        // Auto-refresh every 30 seconds
        setInterval(() => this.refreshData(), 30000);
    }

    async checkApiConnection() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            if (health.status === 'healthy') {
                this.updateConnectionStatus('connected', health.mode || 'online');
            } else {
                this.updateConnectionStatus('error', 'offline');
            }
        } catch (error) {
            this.updateConnectionStatus('error', 'offline');
            console.error('API connection failed:', error);
        }
    }

    updateConnectionStatus(status, mode) {
        const statusElement = $('#connectionStatus');
        const iconClass = status === 'connected' ? 'text-success' : 'text-danger';
        const statusText = status === 'connected' ? 
            `Connected (${mode})` : 'Connection Error';
        
        statusElement.html(`<i class="bi bi-circle-fill ${iconClass}"></i> ${statusText}`);
    }

    async loadFilterOptions() {
        try {
            const [caseTypes, statuses, counties] = await Promise.all([
                fetch('/search/suggest/case-types').then(r => r.json()),
                fetch('/search/suggest/statuses').then(r => r.json()),
                fetch('/search/suggest/counties').then(r => r.json())
            ]);

            this.populateSelect('#caseTypeFilter', caseTypes);
            this.populateSelect('#statusFilter', statuses);
            this.populateSelect('#countyFilter', counties);
        } catch (error) {
            console.log('Filter options not available in offline mode');
        }
    }

    populateSelect(selector, options) {
        const select = $(selector);
        const currentValue = select.val();
        
        // Keep the "All" option and add new options
        select.find('option:not(:first)').remove();
        
        options.forEach(option => {
            select.append(`<option value="${option}">${option}</option>`);
        });
        
        // Restore previous selection if it still exists
        if (currentValue && options.includes(currentValue)) {
            select.val(currentValue);
        }
    }

    async loadCases(page = 1) {
        this.showLoading(true);
        
        try {
            // Build search parameters
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: this.pageSize.toString()
            });

            // Add filters
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value) params.append(key, value);
            });

            const response = await fetch(`/search/?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.cases = data.results || [];
            this.currentPage = data.page || 1;
            this.totalPages = data.total_pages || 1;
            
            this.renderCasesTable();
            this.renderPagination();
            this.updateActiveFilters();
            this.updateStats();
            
        } catch (error) {
            console.error('Failed to load cases:', error);
            this.showError('Failed to load cases. Please try again.');
            this.cases = [];
            this.renderCasesTable();
        } finally {
            this.showLoading(false);
        }
    }

    renderCasesTable() {
        const tbody = $('#casesTableBody');
        tbody.empty();

        if (this.cases.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="bi bi-inbox display-4 text-muted"></i>
                        <p class="mt-2 text-muted">No cases found matching your criteria</p>
                    </td>
                </tr>
            `);
        } else {
            this.cases.forEach(caseItem => {
                const row = this.createCaseRow(caseItem);
                tbody.append(row);
            });
        }

        $('#casesTable').show();
    }

    createCaseRow(caseItem) {
        const statusClass = this.getStatusClass(caseItem.status);
        const filedDate = new Date(caseItem.filed_date).toLocaleDateString();
        
        return `
            <tr class="fade-in">
                <td>
                    <strong>${caseItem.case_number}</strong>
                    <br><small class="text-muted">${caseItem.ucn || ''}</small>
                </td>
                <td>
                    <div class="text-truncate" style="max-width: 200px;" title="${caseItem.description}">
                        ${caseItem.description}
                    </div>
                </td>
                <td><span class="badge bg-secondary">${caseItem.case_type}</span></td>
                <td><span class="status-badge ${statusClass}">${caseItem.status}</span></td>
                <td>${caseItem.judge_name}</td>
                <td>${filedDate}</td>
                <td>${caseItem.county}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="dashboard.viewCase('${caseItem._id}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="dashboard.editCase('${caseItem._id}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="dashboard.deleteCase('${caseItem._id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    getStatusClass(status) {
        const statusMap = {
            'Pending': 'status-pending',
            'Active': 'status-active',
            'Closed': 'status-closed'
        };
        return statusMap[status] || 'status-pending';
    }

    renderPagination() {
        const pagination = $('#pagination');
        pagination.empty();

        if (this.totalPages <= 1) return;

        // Previous button
        pagination.append(`
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.loadCases(${this.currentPage - 1})">Previous</a>
            </li>
        `);

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            pagination.append(`
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="dashboard.loadCases(${i})">${i}</a>
                </li>
            `);
        }

        // Next button
        pagination.append(`
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.loadCases(${this.currentPage + 1})">Next</a>
            </li>
        `);
    }

    performSearch() {
        // Collect all filter values
        this.currentFilters = {
            q: $('#searchInput').val().trim(),
            case_type: $('#caseTypeFilter').val(),
            status: $('#statusFilter').val(),
            county: $('#countyFilter').val(),
            filed_date_from: $('#dateFrom').val(),
            filed_date_to: $('#dateTo').val()
        };

        // Remove empty filters
        Object.keys(this.currentFilters).forEach(key => {
            if (!this.currentFilters[key]) {
                delete this.currentFilters[key];
            }
        });

        this.loadCases(1); // Reset to first page
    }

    clearAllFilters() {
        $('#searchInput, #caseTypeFilter, #statusFilter, #countyFilter, #dateFrom, #dateTo').val('');
        this.currentFilters = {};
        this.loadCases(1);
    }

    updateActiveFilters() {
        const filterChips = $('#filterChips');
        const activeFiltersDiv = $('#activeFilters');
        
        filterChips.empty();
        
        if (Object.keys(this.currentFilters).length === 0) {
            activeFiltersDiv.hide();
            return;
        }

        const filterLabels = {
            q: 'Search',
            case_type: 'Type',
            status: 'Status',
            county: 'County',
            filed_date_from: 'From',
            filed_date_to: 'To'
        };

        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (value) {
                const label = filterLabels[key] || key;
                filterChips.append(`<span class="filter-chip">${label}: ${value}</span>`);
            }
        });

        activeFiltersDiv.show();
    }

    async updateStats() {
        try {
            // Get all cases to calculate stats - use smaller page size
            const response = await fetch('/search/?page=1&page_size=100');
            const data = await response.json();
            const allCases = data.results || [];
            
            // Use total_count from API response which is more accurate
            const totalFromAPI = data.total_count || 0;

            const stats = {
                total: totalFromAPI,
                pending: allCases.filter(c => c.status === 'Pending').length,
                active: allCases.filter(c => c.status === 'Active').length,
                recent: allCases.filter(c => {
                    const filedDate = new Date(c.filed_date);
                    const lastMonth = new Date();
                    lastMonth.setMonth(lastMonth.getMonth() - 1);
                    return filedDate >= lastMonth;
                }).length
            };

            $('#totalCases').text(stats.total);
            $('#pendingCases').text(stats.pending);
            $('#activeCases').text(stats.active);
            $('#recentCases').text(stats.recent);

        } catch (error) {
            console.log('Stats not available in offline mode');
            // Set default values when offline
            $('#totalCases').text('0');
            $('#pendingCases').text('0');
            $('#activeCases').text('0');
            $('#recentCases').text('0');
        }
    }

    async viewCase(caseId) {
        try {
            const response = await fetch(`/cases/${caseId}`);
            const caseData = await response.json();
            
            this.renderCaseDetails(caseData);
            $('#caseDetailModal').modal('show');
        } catch (error) {
            this.showError('Failed to load case details');
        }
    }

    renderCaseDetails(caseData) {
        const content = $('#caseDetailContent');
        
        content.html(`
            <div class="row">
                <div class="col-md-6">
                    <h6>Case Information</h6>
                    <p><strong>Case Number:</strong> ${caseData.case_number}</p>
                    <p><strong>UCN:</strong> ${caseData.ucn}</p>
                    <p><strong>Type:</strong> ${caseData.case_type}</p>
                    <p><strong>Status:</strong> <span class="status-badge ${this.getStatusClass(caseData.status)}">${caseData.status}</span></p>
                </div>
                <div class="col-md-6">
                    <h6>Court Information</h6>
                    <p><strong>Judge:</strong> ${caseData.judge_name}</p>
                    <p><strong>Location:</strong> ${caseData.location}</p>
                    <p><strong>County:</strong> ${caseData.county}</p>
                    <p><strong>Filed Date:</strong> ${new Date(caseData.filed_date).toLocaleDateString()}</p>
                </div>
            </div>
            
            <div class="mt-3">
                <h6>Description</h6>
                <p class="bg-light p-3 rounded">${caseData.description}</p>
            </div>

            <div class="mt-3">
                <h6>Parties</h6>
                ${caseData.parties.map(party => `
                    <div class="party-card">
                        <strong>${party.name}</strong> (${party.type})
                        ${party.attorney ? `<br><small>Attorney: ${party.attorney}${party.atty_phone ? ` - ${party.atty_phone}` : ''}</small>` : ''}
                    </div>
                `).join('')}
            </div>

            <div class="mt-3">
                <h6>Documents</h6>
                ${caseData.documents.map(doc => `
                    <div class="document-item">
                        <strong>${doc.description}</strong> (${doc.pages} pages)
                        <br><small>Date: ${doc.date}</small>
                        ${doc.doc_link ? `<br><a href="${doc.doc_link}" target="_blank" class="btn btn-sm btn-outline-primary mt-1">
                            <i class="bi bi-download"></i> View Document
                        </a>` : ''}
                    </div>
                `).join('')}
            </div>
        `);
    }

    showAddCaseModal() {
        this.editingCaseId = null;
        $('#addCaseModalTitle').text('Add New Case');
        $('#caseForm')[0].reset();
        $('#addCaseModal').modal('show');
    }

    async editCase(caseId) {
        try {
            const response = await fetch(`/cases/${caseId}`);
            const caseData = await response.json();
            
            this.editingCaseId = caseId;
            $('#addCaseModalTitle').text('Edit Case');
            
            // Populate form with case data
            $('#caseNumber').val(caseData.case_number);
            $('#caseType').val(caseData.case_type);
            $('#caseDescription').val(caseData.description);
            $('#caseStatus').val(caseData.status);
            $('#judgeCase').val(caseData.judge_name);
            $('#filedDate').val(caseData.filed_date);
            $('#caseCounty').val(caseData.county);
            $('#caseLocation').val(caseData.location);
            
            $('#addCaseModal').modal('show');
        } catch (error) {
            this.showError('Failed to load case for editing');
        }
    }

    async saveCase() {
        const formData = {
            case_number: $('#caseNumber').val(),
            description: $('#caseDescription').val(),
            location: $('#caseLocation').val(),
            ucn: `${Date.now()}UCN`, // Generate UCN
            case_type: $('#caseType').val(),
            status: $('#caseStatus').val(),
            judge_name: $('#judgeCase').val(),
            filed_date: $('#filedDate').val(),
            parties: [],
            documents: [],
            'actor-id': '999999',
            county: $('#caseCounty').val(),
            'court-id': 'DEFAULT-COURT',
            crawled_date: new Date().toISOString()
        };

        try {
            const url = this.editingCaseId ? `/cases/${this.editingCaseId}` : '/cases/';
            const method = this.editingCaseId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                $('#addCaseModal').modal('hide');
                this.showSuccess(this.editingCaseId ? 'Case updated successfully' : 'Case added successfully');
                this.loadCases(this.currentPage);
                this.updateStats();
            } else {
                const error = await response.text();
                this.showError(`Failed to save case: ${error}`);
            }
        } catch (error) {
            this.showError('Failed to save case. Please try again.');
        }
    }

    async deleteCase(caseId) {
        if (!confirm('Are you sure you want to delete this case?')) return;

        try {
            const response = await fetch(`/cases/${caseId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Case deleted successfully');
                this.loadCases(this.currentPage);
                this.updateStats();
            } else {
                this.showError('Failed to delete case');
            }
        } catch (error) {
            this.showError('Failed to delete case. Please try again.');
        }
    }

    async exportCases() {
        try {
            const response = await fetch('/search/?page_size=10000');
            const data = await response.json();
            
            // Convert to CSV
            const csv = this.convertToCSV(data.results);
            this.downloadCSV(csv, 'legal_cases.csv');
            
            this.showSuccess('Cases exported successfully');
        } catch (error) {
            this.showError('Failed to export cases');
        }
    }

    convertToCSV(cases) {
        const headers = ['Case Number', 'Description', 'Type', 'Status', 'Judge', 'Filed Date', 'County', 'Location'];
        const rows = cases.map(c => [
            c.case_number,
            c.description,
            c.case_type,
            c.status,
            c.judge_name,
            c.filed_date,
            c.county,
            c.location
        ]);
        
        return [headers, ...rows].map(row => 
            row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
        ).join('\n');
    }

    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    editCurrentCase() {
        $('#caseDetailModal').modal('hide');
        // Implementation depends on having access to current case ID
    }

    async refreshData() {
        await this.loadCases(this.currentPage);
        await this.updateStats();
        await this.loadFilterOptions();
    }

    showLoading(show) {
        if (show) {
            $('.loading-spinner').show();
            $('#casesTable').hide();
        } else {
            $('.loading-spinner').hide();
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type) {
        const toastClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const toast = $(`
            <div class="toast position-fixed top-0 end-0 m-3 ${toastClass} text-white" role="alert">
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `);
        
        $('body').append(toast);
        toast.toast({ delay: 3000 });
        toast.toast('show');
        
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
}

// Initialize dashboard when page loads
let dashboard;
$(document).ready(() => {
    dashboard = new LegalCasesDashboard();
});