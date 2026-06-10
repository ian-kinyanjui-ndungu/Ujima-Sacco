/**
 * Ujima SACCO Frontend - Main JavaScript
 * Handles API interactions and dynamic content
 */

// API Base URL
const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Load telemetry data and update stats on home page
 */
async function loadTelemetryData() {
    try {
        const response = await fetch(`${API_BASE_URL}/telemetry/status`);
        
        if (!response.ok) {
            console.error('Failed to fetch telemetry data');
            return;
        }

        const data = await response.json();

        // Update stats
        const metrics = data.aggregate_metrics || {};
        const totalApps = document.getElementById('total-apps');
        const approvedApps = document.getElementById('approved-apps');
        const activeMembers = document.getElementById('active-members');
        const systemStatus = document.getElementById('system-status');

        if (totalApps) totalApps.textContent = metrics.total_applications || 0;
        if (approvedApps) approvedApps.textContent = metrics.approved_loans || 0;
        if (activeMembers) activeMembers.textContent = Object.keys(data.sovereign_configuration || {}).length;
        if (systemStatus) systemStatus.textContent = '✓ Active';

    } catch (error) {
        console.error('Error loading telemetry data:', error);
    }
}

/**
 * Format currency
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES'
    }).format(value);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-KE', options);
}

/**
 * Show loading spinner
 */
function showLoader(element) {
    element.innerHTML = '<div class="spinner">Loading...</div>';
}

/**
 * Hide loading spinner
 */
function hideLoader(element) {
    element.innerHTML = '';
}

/**
 * Get loan status badge
 */
function getStatusBadge(status) {
    const badgeClass = {
        'approved': 'status-active',
        'denied': 'alert-danger',
        'pending': 'alert-warning',
        'escalated': 'alert-warning'
    };

    return `<span class="status-badge ${badgeClass[status] || 'alert-info'}">${status.toUpperCase()}</span>`;
}

/**
 * Validate loan amount
 */
function validateLoanAmount(amount) {
    const min = 1000;
    const max = 500000;

    if (amount < min || amount > max) {
        return {
            valid: false,
            message: `Loan amount must be between KES ${min.toLocaleString()} and KES ${max.toLocaleString()}`
        };
    }

    return { valid: true };
}

/**
 * Validate repayment date
 */
function validateRepaymentDate(dateString) {
    const repaymentDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (repaymentDate <= today) {
        return {
            valid: false,
            message: 'Repayment date must be in the future'
        };
    }

    const maxDate = new Date(today);
    maxDate.setFullYear(maxDate.getFullYear() + 5);

    if (repaymentDate > maxDate) {
        return {
            valid: false,
            message: 'Repayment date cannot be more than 5 years in the future'
        };
    }

    return { valid: true };
}

/**
 * Parse child ages from string
 */
function parseChildAges(agesString) {
    if (!agesString || !agesString.trim()) {
        return [];
    }

    return agesString
        .split(',')
        .map(age => parseInt(age.trim()))
        .filter(age => !isNaN(age) && age > 0 && age < 100);
}

/**
 * Calculate financial health score
 */
function calculateFinancialScore(profile) {
    let score = 50; // Base score

    // Income factors
    const totalIncome = (profile.monthly_salary || 0) + (profile.average_harvest_income || 0);
    if (totalIncome > 50000) score += 20;
    else if (totalIncome > 10000) score += 10;

    // Token balance factor
    if (profile.current_token_balance > 5000) score += 15;
    else if (profile.current_token_balance > 1000) score += 5;

    // Employment stability
    if (profile.is_salaried) score += 10;

    return Math.min(score, 100);
}

/**
 * Format member state for display
 */
function formatMemberState(state) {
    return {
        member_id: state.member_id,
        conversation_history: state.conversation_history || [],
        current_agent: state.current_agent || 'unknown',
        loan_application: state.loan_application,
        human_escalation_status: state.human_escalation_status || 'inactive',
        financial_stress_flags: state.financial_stress_flags || []
    };
}

/**
 * Get agent display name
 */
function getAgentName(agentId) {
    const names = {
        'scout': '🔍 Scout (Financial Coach)',
        'guardian': '👨‍⚖️ Guardian (Risk Assessor)',
        'hunter': '🎯 Hunter (Anomaly Detector)'
    };

    return names[agentId] || agentId;
}

/**
 * Handle API errors
 */
function handleApiError(error, context = '') {
    console.error(`API Error${context ? ' (' + context + ')' : ''}:`, error);

    let message = 'An error occurred';

    if (error instanceof fetch.Error) {
        message = 'Network error - please check your connection';
    } else if (error.message) {
        message = error.message;
    }

    return message;
}

/**
 * Fetch member data from backend
 */
async function fetchMemberData(memberId) {
    try {
        // Since the backend doesn't have a /member endpoint, we'll simulate with conversation
        const testResponse = await fetch(`${API_BASE_URL}/`, {
            method: 'GET'
        });

        if (!testResponse.ok) {
            throw new Error('Failed to connect to backend');
        }

        return {
            member_id: memberId,
            name: 'Member Name',
            sub_county: 'Busia Central',
            current_token_balance: 0,
            monthly_salary: 0,
            average_harvest_income: 0,
            crop_type: null,
            financial_stress_flags: []
        };
    } catch (error) {
        console.error('Error fetching member data:', error);
        return null;
    }
}

/**
 * Send SMS message to backend
 */
async function sendSmsToBackend(memberId, message, subCounty = 'Busia Central') {
    try {
        const response = await fetch(`${API_BASE_URL}/sms/inbound`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                member_id: memberId,
                text: message,
                sub_county: subCounty
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error sending SMS:', error);
        throw error;
    }
}

/**
 * Get human review queue
 */
async function getHumanQueue() {
    try {
        const response = await fetch(`${API_BASE_URL}/human/queue`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching human queue:', error);
        return [];
    }
}

/**
 * Submit human decision
 */
async function submitHumanDecision(memberId, decision, reason) {
    try {
        const response = await fetch(`${API_BASE_URL}/human/takeover`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                member_id: memberId,
                decision: decision,
                reason: reason
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error submitting decision:', error);
        throw error;
    }
}

/**
 * Get system telemetry
 */
async function getSystemTelemetry() {
    try {
        const response = await fetch(`${API_BASE_URL}/telemetry/status`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching telemetry:', error);
        return null;
    }
}

/**
 * Initialize page on load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load telemetry data if stats elements exist
    if (document.getElementById('total-apps')) {
        loadTelemetryData();

        // Refresh every 30 seconds
        setInterval(loadTelemetryData, 30000);
    }
});

/**
 * Accessibility - Improve keyboard navigation
 */
document.addEventListener('keydown', function(e) {
    // Escape key to close modals
    if (e.key === 'Escape') {
        const modal = document.querySelector('.modal[style*="display: block"]');
        if (modal) {
            modal.style.display = 'none';
        }
    }
});

/**
 * Smooth scroll for anchor links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href && href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
});

/**
 * Export functions for global access
 */
window.ujimaSacco = {
    loadTelemetryData,
    formatCurrency,
    formatDate,
    validateLoanAmount,
    validateRepaymentDate,
    parseChildAges,
    calculateFinancialScore,
    getAgentName,
    fetchMemberData,
    sendSmsToBackend,
    getHumanQueue,
    submitHumanDecision,
    getSystemTelemetry
};
