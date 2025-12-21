import { useState } from 'react';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Shield, Lock } from 'lucide-react';
import { uploadFile, protectFile, downloadProtectedFile } from '../services/api';

const Upload = () => {
    const [file, setFile] = useState(null);
    const [company, setCompany] = useState('');
    const [department, setDepartment] = useState('HR');
    const [uploaderEmail, setUploaderEmail] = useState('');
    const [uploaderName, setUploaderName] = useState('');
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [protecting, setProtecting] = useState(false);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setUploadResult(null);
    };

    const handleUpload = async (e) => {
        e.preventDefault();

        if (!file || !company || !uploaderEmail) {
            alert('Please select a file, enter company name and your email');
            return;
        }

        setUploading(true);

        try {
            const result = await uploadFile(file, company, department, uploaderEmail, uploaderName);
            setUploadResult(result);
            setFile(null);
            // Reset form
            document.getElementById('file-input').value = '';
        } catch (error) {
            console.error('Upload error:', error);
            alert('Upload failed: ' + (error.response?.data?.detail || error.message));
        } finally {
            setUploading(false);
        }
    };

    const handleProtect = async (mask, encrypt) => {
        if (!uploadResult?.file_id) return;

        setProtecting(true);

        try {
            await protectFile(uploadResult.file_id, mask, encrypt);
            alert(`File protected successfully with ${mask ? 'masking' : ''} ${mask && encrypt ? 'and' : ''} ${encrypt ? 'encryption' : ''}`);
        } catch (error) {
            console.error('Protection error:', error);
            alert('Protection failed: ' + (error.response?.data?.detail || error.message));
        } finally {
            setProtecting(false);
        }
    };

    const getClassificationColor = (classification) => {
        const colors = {
            'Public': 'text-green-400 bg-green-400/10 border-green-400/30',
            'Internal': 'text-blue-400 bg-blue-400/10 border-blue-400/30',
            'Confidential': 'text-orange-400 bg-orange-400/10 border-orange-400/30',
            'Restricted': 'text-red-400 bg-red-400/10 border-red-400/30',
        };
        return colors[classification] || 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-4xl font-bold text-white mb-2">Upload & Scan Files</h1>
                <p className="text-secondary-400">Upload files to detect sensitive data and classify security levels</p>
            </div>

            {/* Upload Card */}
            <div className="card max-w-3xl mx-auto">
                <form onSubmit={handleUpload}>
                    <div className="space-y-6">
                        {/* Company Input */}
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Company Name
                            </label>
                            <input
                                type="text"
                                value={company}
                                onChange={(e) => setCompany(e.target.value)}
                                className="input-field"
                                placeholder="Enter company name"
                                required
                            />
                        </div>

                        {/* Department Select */}
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Department
                            </label>
                            <select
                                value={department}
                                onChange={(e) => setDepartment(e.target.value)}
                                className="input-field"
                            >
                                <option value="HR">HR</option>
                                <option value="Finance">Finance</option>
                                <option value="Sales">Sales</option>
                                <option value="IT">IT</option>
                                <option value="Legal">Legal</option>
                                <option value="Marketing">Marketing</option>
                                <option value="Operations">Operations</option>
                            </select>
                        </div>

                        {/* Uploader Email Input */}
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Your Email <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="email"
                                value={uploaderEmail}
                                onChange={(e) => setUploaderEmail(e.target.value)}
                                className="input-field"
                                placeholder="your.email@company.com"
                                required
                            />
                            <p className="text-xs text-secondary-500 mt-1">
                                Required for file access control
                            </p>
                        </div>

                        {/* Uploader Name Input */}
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Your Name (Optional)
                            </label>
                            <input
                                type="text"
                                value={uploaderName}
                                onChange={(e) => setUploaderName(e.target.value)}
                                className="input-field"
                                placeholder="Your full name"
                            />
                        </div>

                        {/* File Upload */}
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Select File
                            </label>
                            <div className="relative">
                                <input
                                    id="file-input"
                                    type="file"
                                    onChange={handleFileChange}
                                    className="input-field cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-600 file:text-white hover:file:bg-primary-700"
                                    accept=".txt,.csv,.pdf,.docx"
                                />
                            </div>
                            {file && (
                                <div className="mt-2 flex items-center space-x-2 text-sm text-secondary-400">
                                    <FileText className="h-4 w-4" />
                                    <span>{file.name} ({(file.size / 1024).toFixed(2)} KB)</span>
                                </div>
                            )}
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={uploading || !file || !company || !uploaderEmail}
                            className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <UploadIcon className="h-5 w-5" />
                            <span>{uploading ? 'Uploading & Scanning...' : 'Upload & Scan'}</span>
                        </button>
                    </div>
                </form>
            </div>

            {/* Results Card */}
            {uploadResult && (
                <div className="card max-w-3xl mx-auto animate-fadeIn">
                    <div className="flex items-start space-x-4">
                        <CheckCircle className="h-8 w-8 text-green-400 flex-shrink-0" />
                        <div className="flex-1">
                            <h3 className="text-xl font-semibold text-white mb-4">Scan Complete</h3>

                            {/* File Info */}
                            <div className="bg-secondary-700/50 rounded-lg p-4 mb-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-secondary-400">File Name</p>
                                        <p className="text-white font-medium">{uploadResult.metadata.original_filename}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-secondary-400">File ID</p>
                                        <p className="text-white font-mono text-sm">{uploadResult.file_id}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-secondary-400">Company</p>
                                        <p className="text-white">{uploadResult.metadata.company}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-secondary-400">Department</p>
                                        <p className="text-white">{uploadResult.metadata.department}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Classification */}
                            {uploadResult.metadata.classification && (
                                <div className="mb-4">
                                    <p className="text-sm text-secondary-400 mb-2">Classification</p>
                                    <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg border ${getClassificationColor(uploadResult.metadata.classification)}`}>
                                        <Shield className="h-5 w-5" />
                                        <span className="font-semibold">{uploadResult.metadata.classification}</span>
                                    </div>
                                    {uploadResult.metadata.detections_count > 0 && (
                                        <p className="text-sm text-secondary-400 mt-2">
                                            {uploadResult.metadata.detections_count} sensitive item(s) detected
                                        </p>
                                    )}
                                </div>
                            )}

                            {/* Protection Actions */}
                            <div className="border-t border-secondary-700 pt-4">
                                <h4 className="text-sm font-medium text-secondary-300 mb-3">Data Protection</h4>
                                <div className="flex flex-wrap gap-3">
                                    <button
                                        onClick={() => handleProtect(true, false)}
                                        disabled={protecting}
                                        className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        <Shield className="h-4 w-4" />
                                        <span>Mask Sensitive Data</span>
                                    </button>
                                    <button
                                        onClick={() => handleProtect(false, true)}
                                        disabled={protecting}
                                        className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        <Lock className="h-4 w-4" />
                                        <span>Encrypt File</span>
                                    </button>
                                    <button
                                        onClick={() => handleProtect(true, true)}
                                        disabled={protecting}
                                        className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        <Lock className="h-4 w-4" />
                                        <span>Mask & Encrypt</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Info Cards */}
            <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
                <div className="card text-center">
                    <Shield className="h-10 w-10 text-primary-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">AI Detection</h3>
                    <p className="text-sm text-secondary-400">Uses spaCy & HuggingFace for accurate detection</p>
                </div>
                <div className="card text-center">
                    <FileText className="h-10 w-10 text-blue-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">Classification</h3>
                    <p className="text-sm text-secondary-400">Automatic sensitivity level assignment</p>
                </div>
                <div className="card text-center">
                    <Lock className="h-10 w-10 text-orange-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">Protection</h3>
                    <p className="text-sm text-secondary-400">Masking & encryption options</p>
                </div>
            </div>
        </div>
    );
};

export default Upload;
