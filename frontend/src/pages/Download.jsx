import { useState } from 'react';
import { Download as DownloadIcon, Mail, FileText, CheckCircle, XCircle, Info } from 'lucide-react';
import { accessFile, getFileInfo } from '../services/api';

const Download = () => {
    const [fileId, setFileId] = useState('');
    const [requesterEmail, setRequesterEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [fileInfo, setFileInfo] = useState(null);
    const [downloadResult, setDownloadResult] = useState(null);

    const handleGetInfo = async (e) => {
        e.preventDefault();

        if (!fileId) {
            alert('Please enter a file ID');
            return;
        }

        setLoading(true);
        try {
            const info = await getFileInfo(fileId);
            setFileInfo(info);
            setDownloadResult(null);
        } catch (error) {
            console.error('Error fetching file info:', error);
            alert('Failed to get file info: ' + (error.response?.data?.detail || error.message));
            setFileInfo(null);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (e) => {
        e.preventDefault();

        if (!fileId || !requesterEmail) {
            alert('Please enter both file ID and your email');
            return;
        }

        setLoading(true);
        try {
            const result = await accessFile(fileId, requesterEmail);
            setDownloadResult(result);
        } catch (error) {
            console.error('Download error:', error);
            alert('Download failed: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-4xl font-bold text-white mb-2">Download File</h1>
                <p className="text-secondary-400">Access files with email-based permissions</p>
            </div>

            {/* File Info Card */}
            <div className="card max-w-3xl mx-auto">
                <h2 className="text-xl font-semibold text-white mb-4">File Information</h2>
                <form onSubmit={handleGetInfo}>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                File ID
                            </label>
                            <input
                                type="text"
                                value={fileId}
                                onChange={(e) => setFileId(e.target.value)}
                                className="input-field"
                                placeholder="Enter file ID from upload"
                                required
                            />
                            <p className="text-xs text-secondary-500 mt-1">
                                You received this when you uploaded the file
                            </p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || !fileId}
                            className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
                        >
                            <Info className="h-5 w-5" />
                            <span>{loading ? 'Loading...' : 'Get File Info'}</span>
                        </button>
                    </div>
                </form>
            </div>

            {/* File Info Display */}
            {fileInfo && (
                <div className="card max-w-3xl mx-auto">
                    <h3 className="text-lg font-semibold text-white mb-4">File Details</h3>
                    <div className="bg-secondary-700/50 rounded-lg p-4 space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-sm text-secondary-400">Filename</p>
                                <p className="text-white font-medium">{fileInfo.original_filename}</p>
                            </div>
                            <div>
                                <p className="text-sm text-secondary-400">Classification</p>
                                <p className="text-white font-medium">{fileInfo.classification}</p>
                            </div>
                            <div>
                                <p className="text-sm text-secondary-400">Company</p>
                                <p className="text-white">{fileInfo.company}</p>
                            </div>
                            <div>
                                <p className="text-sm text-secondary-400">Department</p>
                                <p className="text-white">{fileInfo.department}</p>
                            </div>
                            {fileInfo.uploader_name && (
                                <div>
                                    <p className="text-sm text-secondary-400">Uploaded By</p>
                                    <p className="text-white">{fileInfo.uploader_name}</p>
                                </div>
                            )}
                            <div>
                                <p className="text-sm text-secondary-400">File Size</p>
                                <p className="text-white">{(fileInfo.file_size / 1024).toFixed(2)} KB</p>
                            </div>
                        </div>

                        {fileInfo.masked_fields && fileInfo.masked_fields.length > 0 && (
                            <div className="border-t border-secondary-600 pt-3 mt-3">
                                <p className="text-sm text-secondary-400 mb-2">Masked Data Types (for non-owners):</p>
                                <div className="flex flex-wrap gap-2">
                                    {fileInfo.masked_fields.map((field, idx) => (
                                        <span key={idx} className="px-3 py-1 bg-orange-400/10 text-orange-400 rounded-full text-sm">
                                            {field}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Download Card */}
            <div className="card max-w-3xl mx-auto">
                <h2 className="text-xl font-semibold text-white mb-4">Download File</h2>
                <form onSubmit={handleDownload}>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-secondary-300 mb-2">
                                Your Email <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="email"
                                value={requesterEmail}
                                onChange={(e) => setRequesterEmail(e.target.value)}
                                className="input-field"
                                placeholder="your.email@company.com"
                                required
                            />
                            <p className="text-xs text-secondary-500 mt-1">
                                If your email matches the uploader's email, you'll get the original file. Otherwise, you'll get the masked version.
                            </p>
                        </div>

                        <div className="bg-blue-400/10 border border-blue-400/30 rounded-lg p-4">
                            <div className="flex items-start space-x-3">
                                <Info className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                                <div className="text-sm text-blue-300">
                                    <p className="font-semibold mb-1">Access Control Rules:</p>
                                    <ul className="list-disc list-inside space-y-1 text-blue-200">
                                        <li>Email matches uploader → <span className="font-semibold">Original file</span></li>
                                        <li>Email doesn't match → <span className="font-semibold">Masked file</span> (name/email preserved, sensitive data hidden)</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || !fileId || !requesterEmail}
                            className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50"
                        >
                            <DownloadIcon className="h-5 w-5" />
                            <span>{loading ? 'Downloading...' : 'Download File'}</span>
                        </button>
                    </div>
                </form>
            </div>

            {/* Download Result */}
            {downloadResult && (
                <div className="card max-w-3xl mx-auto">
                    <div className={`flex items-start space-x-4 ${downloadResult.emailMatch ? 'text-green-400' : 'text-orange-400'}`}>
                        {downloadResult.emailMatch ? (
                            <CheckCircle className="h-8 w-8 flex-shrink-0" />
                        ) : (
                            <Info className="h-8 w-8 flex-shrink-0" />
                        )}
                        <div className="flex-1">
                            <h3 className="text-xl font-semibold text-white mb-2">Download Complete</h3>
                            <p className="text-secondary-300 mb-3">
                                File downloaded: <span className="font-mono text-sm">{downloadResult.filename}</span>
                            </p>

                            {downloadResult.emailMatch ? (
                                <div className="bg-green-400/10 border border-green-400/30 rounded-lg p-4">
                                    <p className="text-green-300 font-semibold mb-1">✓ Original File</p>
                                    <p className="text-green-200 text-sm">
                                        Your email matched the uploader's email. You received the original file with all data intact.
                                    </p>
                                </div>
                            ) : (
                                <div className="bg-orange-400/10 border border-orange-400/30 rounded-lg p-4">
                                    <p className="text-orange-300 font-semibold mb-1">⚠ Masked File</p>
                                    <p className="text-orange-200 text-sm">
                                        Your email did not match the uploader's email. You received a masked version where sensitive data (phone numbers, credit cards, SSNs, etc.) has been replaced with [MASKED] placeholders. Names and emails are preserved.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Info Cards */}
            <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
                <div className="card text-center">
                    <Mail className="h-10 w-10 text-primary-500 mx-auto mb-3"

                    />
                    <h3 className="text-lg font-semibold text-white mb-2">Email-Based Access</h3>
                    <p className="text-sm text-secondary-400">Secure file access controlled by email matching</p>
                </div>
                <div className="card text-center">
                    <FileText className="h-10 w-10 text-blue-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">Dual Versions</h3>
                    <p className="text-sm text-secondary-400">Original and masked copies automatically created</p>
                </div>
                <div className="card text-center">
                    <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">Smart Masking</h3>
                    <p className="text-sm text-secondary-400">Preserves names/emails, masks sensitive data</p>
                </div>
            </div>
        </div>
    );
};

export default Download;
