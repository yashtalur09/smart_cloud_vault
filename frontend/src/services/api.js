/**
 * API Service for SmartCloud Vault
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// File Upload
export const uploadFile = async (file, company, department, uploaderEmail, uploaderName = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company', company);
    formData.append('department', department);
    formData.append('uploader_email', uploaderEmail);
    if (uploaderName) {
        formData.append('uploader_name', uploaderName);
    }

    const response = await api.post('/api/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

// Get file list
export const getFiles = async (company = null, department = null) => {
    const params = {};
    if (company) params.company = company;
    if (department) params.department = department;

    const response = await api.get('/api/upload/files', { params });
    return response.data;
};

// Get file details
export const getFileDetails = async (fileId) => {
    const response = await api.get(`/api/upload/files/${fileId}`);
    return response.data;
};

// Access file with email-based control
export const accessFile = async (fileId, requesterEmail) => {
    const response = await api.post('/api/files/access', {
        file_id: fileId,
        requester_email: requesterEmail
    }, {
        responseType: 'blob',
    });

    // Get filename from headers if available
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'download';
    if (contentDisposition) {
        const matches = /filename="(.+)"/.exec(contentDisposition);
        if (matches && matches[1]) {
            filename = matches[1];
        }
    }

    // Check which version was returned
    const fileType = response.headers['x-file-type'] || 'unknown';
    const emailMatch = response.headers['x-email-match'] === 'true';

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();

    return { fileType, emailMatch, filename };
};

// Get file info without downloading
export const getFileInfo = async (fileId) => {
    const response = await api.get(`/api/files/info/${fileId}`);
    return response.data;
};

// Protect file
export const protectFile = async (fileId, mask = true, encrypt = false) => {
    const response = await api.post(`/api/protect/${fileId}`, null, {
        params: { mask, encrypt },
    });
    return response.data;
};

// Download protected file
export const downloadProtectedFile = async (fileId) => {
    const response = await api.get(`/api/protect/${fileId}/download`, {
        responseType: 'blob',
    });
    return response.data;
};

// Analysis
export const getCompanyAnalysis = async (company) => {
    const response = await api.get('/api/analysis/company', {
        params: { company },
    });
    return response.data;
};

export const getDepartmentAnalysis = async (company, department) => {
    const response = await api.get('/api/analysis/department', {
        params: { company, department },
    });
    return response.data;
};

export const getOverview = async () => {
    const response = await api.get('/api/analysis/overview');
    return response.data;
};

export const listCompanies = async () => {
    const response = await api.get('/api/analysis/companies');
    return response.data;
};

export const listDepartments = async (company = null) => {
    const params = company ? { company } : {};
    const response = await api.get('/api/analysis/departments', { params });
    return response.data;
};

// Recommendations
export const generateRecommendations = async (company, department = null) => {
    const params = { company };
    if (department) params.department = department;

    const response = await api.post('/api/recommendations/generate', null, { params });
    return response.data;
};

export const getRecommendations = async (company, department = null, priority = null) => {
    const params = { company };
    if (department) params.department = department;
    if (priority) params.priority = priority;

    const response = await api.get('/api/recommendations', { params });
    return response.data;
};

// Reports
export const generateReport = async (company, department = null, includeCharts = true, includeRecommendations = true) => {
    const params = {
        company,
        include_charts: includeCharts,
        include_recommendations: includeRecommendations,
    };
    if (department) params.department = department;

    const response = await api.post('/api/reports/generate', null, { params });
    return response.data;
};

export const downloadReport = async (reportId) => {
    const response = await api.get(`/api/reports/download/${reportId}`, {
        responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `compliance_report_${reportId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
};

export const listReports = async (company = null) => {
    const params = company ? { company } : {};
    const response = await api.get('/api/reports/list', { params });
    return response.data;
};

// Health check
export const getHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

export default api;
