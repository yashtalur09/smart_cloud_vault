import { useState } from 'react';
import { Download as DownloadIcon, User, Shield, FileText, Search, CheckCircle, XCircle } from 'lucide-react';
import { employeeAccessFile, authorityAccessFile, listEmployeeFiles } from '../services/api';

const DownloadRoleBased = () => {
    const [accessType, setAccessType] = useState('employee'); // 'employee' or 'authority'
    
    // Employee fields
    const [employeeId, setEmployeeId] = useState('');
    const [employeeName, setEmployeeName] = useState('');
    const [employeeEmail, setEmployeeEmail] = useState('');
    const [employeeFileId, setEmployeeFileId] = useState('');
    
    // Authority fields
    const [authorityName, setAuthorityName] = useState('');
    const [authorityEmail, setAuthorityEmail] = useState('');
    const [authorityRole, setAuthorityRole] = useState('hr');
    const [targetEmployeeId, setTargetEmployeeId] = useState('');
    const [authorityFileId, setAuthorityFileId] = useState('');
    
    // Employee file list
    const [employeeFiles, setEmployeeFiles] = useState(null);
    const [loadingFiles, setLoadingFiles] = useState(false);
    
    const [loading, setLoading] = useState(false);
    const [downloadResult, setDownloadResult] = useState(null);

    const handleEmployeeListFiles = async (e) => {
        e.preventDefault();

        if (!employeeId || !employeeName || !employeeEmail) {
            alert('Please fill in all employee fields');
            return;
        }

        setLoadingFiles(true);
        setEmployeeFiles(null);
        setDownloadResult(null);

        try {
            const result = await listEmployeeFiles(employeeId);
            setEmployeeFiles(result);
        } catch (error) {
            console.error('Error listing files:', error);
            setDownloadResult({
                success: false,
                message: 'Failed to list files: ' + (error.response?.data?.detail || error.message),
                type: 'employee'
            });
        } finally {
            setLoadingFiles(false);
        }
    };

    const handleAuthorityDownload = async (e) => {
        e.preventDefault();

        if (!authorityName || !authorityEmail || !targetEmployeeId || !authorityFileId) {
            alert('Please fill in all authority fields');
            return;
        }

        setLoading(true);
        setDownloadResult(null);

        try {
            const result = await authorityAccessFile(
                authorityName, 
                authorityEmail, 
                authorityRole, 
                targetEmployeeId, 
                authorityFileId
            );
            setDownloadResult({
                success: true,
                message: `Successfully downloaded masked file: ${result.filename}`,
                type: 'authority'
            });
        } catch (error) {
            console.error('Authority download error:', error);
            setDownloadResult({
                success: false,
                message: 'Download failed: ' + (error.response?.data?.detail || error.message),
                type: 'authority'
            });
        } finally {
            setLoading(false);
        }
    };

    const handleListEmployeeFiles = async () => {
        if (!employeeId || !employeeName || !employeeEmail) {
            alert('Please fill in all employee fields');
            return;
        }

        setLoadingFiles(true);
        setEmployeeFiles(null);
        setDownloadResult(null);

        try {
            const result = await listEmployeeFiles(employeeId);
            setEmployeeFiles(result);
        } catch (error) {
            console.error('Error listing files:', error);
            setDownloadResult({
                success: false,
                message: 'Failed to list files: ' + (error.response?.data?.detail || error.message),
                type: 'employee'
            });
        } finally {
            setLoadingFiles(false);
        }
    };

    const handleListAuthorityFiles = async (e) => {
        e.preventDefault();

        if (!authorityName || !authorityEmail || !targetEmployeeId) {
            alert('Please fill in all required fields');
            return;
        }

        setLoadingFiles(true);
        setEmployeeFiles(null);
        setDownloadResult(null);

        try {
            const result = await listEmployeeFiles(targetEmployeeId);
            setEmployeeFiles(result);
        } catch (error) {
            console.error('Error listing files:', error);
            setDownloadResult({
                success: false,
                message: 'Failed to list files: ' + (error.response?.data?.detail || error.message),
                type: 'authority'
            });
        } finally {
            setLoadingFiles(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-4xl font-bold text-white mb-2">Role-Based File Access</h1>
                <p className="text-secondary-400">Download files based on your role</p>
            </div>

            {/* Role Selection */}
            <div className="card max-w-3xl mx-auto">
                <h2 className="text-xl font-semibold text-white mb-4">Select Access Type</h2>
                <div className="grid grid-cols-2 gap-4">
                    <button
                        onClick={() => {
                            setAccessType('employee');
                            setDownloadResult(null);
                            setEmployeeFiles(null);
                        }}
                        className={`p-6 rounded-lg border-2 transition-all ${
                            accessType === 'employee'
                                ? 'border-primary-500 bg-primary-500/10'
                                : 'border-secondary-600 hover:border-secondary-500'
                        }`}
                    >
                        <User className="h-8 w-8 mx-auto mb-2 text-primary-400" />
                        <h3 className="text-lg font-semibold text-white">Employee</h3>
                        <p className="text-sm text-secondary-400 mt-2">
                            Access your own files (original versions)
                        </p>
                    </button>

                    <button
                        onClick={() => {
                            setAccessType('authority');
                            setDownloadResult(null);
                            setEmployeeFiles(null);
                        }}
                        className={`p-6 rounded-lg border-2 transition-all ${
                            accessType === 'authority'
                                ? 'border-primary-500 bg-primary-500/10'
                                : 'border-secondary-600 hover:border-secondary-500'
                        }`}
                    >
                        <Shield className="h-8 w-8 mx-auto mb-2 text-orange-400" />
                        <h3 className="text-lg font-semibold text-white">Company Authority</h3>
                        <p className="text-sm text-secondary-400 mt-2">
                            HR/Admin/Auditor access (masked versions)
                        </p>
                    </button>
                </div>
            </div>

            {/* Employee Access Form */}
            {accessType === 'employee' && (
                <div className="card max-w-3xl mx-auto">
                    <div className="flex items-center space-x-2 mb-4">
                        <User className="h-6 w-6 text-primary-400" />
                        <h2 className="text-xl font-semibold text-white">Employee File Access</h2>
                    </div>
                    
                    <form onSubmit={handleEmployeeListFiles}>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Employee ID <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={employeeId}
                                    onChange={(e) => setEmployeeId(e.target.value)}
                                    className="input-field"
                                    placeholder="e.g., EMP12345"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Employee Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={employeeName}
                                    onChange={(e) => setEmployeeName(e.target.value)}
                                    className="input-field"
                                    placeholder="Your full name"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Employee Email <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="email"
                                    value={employeeEmail}
                                    onChange={(e) => setEmployeeEmail(e.target.value)}
                                    className="input-field"
                                    placeholder="your.email@company.com"
                                    required
                                />
                            </div>

                            <button
                                type="button"
                                onClick={handleListEmployeeFiles}
                                disabled={loadingFiles || !employeeId || !employeeName || !employeeEmail}
                                className="w-full btn-primary flex items-center justify-center space-x-2"
                            >
                                <Search className="h-5 w-5" />
                                <span>{loadingFiles ? 'Loading...' : 'List My Files'}</span>
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Authority Access Form */}
            {accessType === 'authority' && (
                <div className="card max-w-3xl mx-auto">
                    <div className="flex items-center space-x-2 mb-4">
                        <Shield className="h-6 w-6 text-orange-400" />
                        <h2 className="text-xl font-semibold text-white">Authority File Access</h2>
                    </div>
                    
                    <form onSubmit={handleListAuthorityFiles}>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Your Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={authorityName}
                                    onChange={(e) => setAuthorityName(e.target.value)}
                                    className="input-field"
                                    placeholder="Your full name"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Your Email <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="email"
                                    value={authorityEmail}
                                    onChange={(e) => setAuthorityEmail(e.target.value)}
                                    className="input-field"
                                    placeholder="your.email@company.com"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-secondary-300 mb-2">
                                    Your Role <span className="text-red-400">*</span>
                                </label>
                                <select
                                    value={authorityRole}
                                    onChange={(e) => setAuthorityRole(e.target.value)}
                                    className="input-field"
                                    required
                                >
                                    <option value="hr">HR</option>
                                    <option value="admin">Admin</option>
                                    <option value="auditor">Auditor</option>
                                </select>
                            </div>

                            <div className="border-t border-secondary-700 pt-4">
                                <h3 className="text-sm font-semibold text-white mb-3">Employee Information</h3>
                                
                                <div>
                                    <label className="block text-sm font-medium text-secondary-300 mb-2">
                                        Employee ID <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={targetEmployeeId}
                                        onChange={(e) => setTargetEmployeeId(e.target.value)}
                                        className="input-field"
                                        placeholder="e.g., EMP12345"
                                        required
                                    />
                                    <p className="text-xs text-secondary-500 mt-1">
                                        Enter the employee ID to view their files
                                    </p>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loadingFiles || !authorityName || !authorityEmail || !targetEmployeeId}
                                className="w-full btn-primary flex items-center justify-center space-x-2 bg-orange-600 hover:bg-orange-700"
                            >
                                <Search className="h-5 w-5" />
                                <span>{loadingFiles ? 'Loading...' : 'List Employee Files'}</span>
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Employee Files List */}
            {employeeFiles && (
                <div className="card max-w-3xl mx-auto">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        Files for Employee: {employeeFiles.employee_id}
                    </h3>
                    
                    {employeeFiles.employee_name && (
                        <p className="text-secondary-400 mb-4">
                            {employeeFiles.employee_name} ({employeeFiles.employee_email})
                        </p>
                    )}
                    
                    {employeeFiles.total_count === 0 ? (
                        <p className="text-secondary-500">No files found for this employee.</p>
                    ) : (
                        <div className="space-y-3">
                            {employeeFiles.files.map((file) => (
                                <div
                                    key={file.file_id}
                                    className="bg-secondary-700/50 rounded-lg p-4 hover:bg-secondary-700/70 transition-colors"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2">
                                                <FileText className="h-4 w-4 text-primary-400" />
                                                <span className="text-white font-medium">
                                                    {file.original_filename}
                                                </span>
                                                {file.document_name && (
                                                    <span className="text-xs text-secondary-400">
                                                        ({file.document_name})
                                                    </span>
                                                )}
                                            </div>
                                            <div className="mt-2 text-xs text-secondary-500 space-y-1">
                                                <div>File ID: {file.file_id}</div>
                                                <div>Uploaded: {new Date(file.upload_date).toLocaleString()}</div>
                                                {file.classification && (
                                                    <div>Classification: {file.classification}</div>
                                                )}
                                                {file.file_size && (
                                                    <div>Size: {(file.file_size / 1024).toFixed(2)} KB</div>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            onClick={async () => {
                                                try {
                                                    setLoading(true);
                                                    let result;
                                                    if (accessType === 'employee') {
                                                        result = await employeeAccessFile(
                                                            employeeId,
                                                            employeeName,
                                                            employeeEmail,
                                                            file.file_id
                                                        );
                                                    } else {
                                                        // Use employee_id from the file list response, not the form state
                                                        result = await authorityAccessFile(
                                                            authorityName,
                                                            authorityEmail,
                                                            authorityRole,
                                                            employeeFiles.employee_id,
                                                            file.file_id
                                                        );
                                                    }
                                                    setDownloadResult({
                                                        success: true,
                                                        message: `Successfully downloaded: ${result.filename}`,
                                                        type: accessType
                                                    });
                                                } catch (error) {
                                                    console.error('Download error:', error);
                                                    setDownloadResult({
                                                        success: false,
                                                        message: 'Download failed: ' + (error.response?.data?.detail || error.message),
                                                        type: accessType
                                                    });
                                                } finally {
                                                    setLoading(false);
                                                }
                                            }}
                                            disabled={loading}
                                            className={`btn-primary flex items-center space-x-2 whitespace-nowrap ${
                                                accessType === 'authority' ? 'bg-orange-600 hover:bg-orange-700' : ''
                                            }`}
                                        >
                                            <DownloadIcon className="h-4 w-4" />
                                            <span>{accessType === 'authority' ? 'Download (Masked)' : 'Download'}</span>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Download Result */}
            {downloadResult && (
                <div className={`card max-w-3xl mx-auto ${
                    downloadResult.success ? 'border-green-500/30' : 'border-red-500/30'
                }`}>
                    <div className="flex items-start space-x-3">
                        {downloadResult.success ? (
                            <CheckCircle className="h-6 w-6 text-green-400 flex-shrink-0" />
                        ) : (
                            <XCircle className="h-6 w-6 text-red-400 flex-shrink-0" />
                        )}
                        <div>
                            <h3 className={`text-lg font-semibold ${
                                downloadResult.success ? 'text-green-400' : 'text-red-400'
                            }`}>
                                {downloadResult.success ? 'Success' : 'Error'}
                            </h3>
                            <p className="text-secondary-300 mt-1">{downloadResult.message}</p>
                            {downloadResult.success && (
                                <p className="text-xs text-secondary-500 mt-2">
                                    File type: {downloadResult.type === 'employee' ? 'Original (from original bucket)' : 'Masked (from masked bucket)'}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DownloadRoleBased;
