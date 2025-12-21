import { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Building2, Users, FileText, Download, TrendingUp, AlertTriangle } from 'lucide-react';
import { getCompanyAnalysis, getDepartmentAnalysis, listCompanies, generateReport, downloadReport } from '../services/api';

const Dashboard = () => {
    const [companies, setCompanies] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState('');
    const [companyAnalysis, setCompanyAnalysis] = useState(null);
    const [departmentAnalyses, setDepartmentAnalyses] = useState([]);
    const [loading, setLoading] = useState(false);
    const [generatingReport, setGeneratingReport] = useState(false);

    useEffect(() => {
        loadCompanies();
    }, []);

    useEffect(() => {
        if (selectedCompany) {
            loadAnalysis();
        }
    }, [selectedCompany]);

    const loadCompanies = async () => {
        try {
            const data = await listCompanies();
            setCompanies(data.companies || []);
            if (data.companies && data.companies.length > 0) {
                setSelectedCompany(data.companies[0]);
            }
        } catch (error) {
            console.error('Error loading companies:', error);
        }
    };

    const loadAnalysis = async () => {
        if (!selectedCompany) return;

        setLoading(true);
        try {
            // Get company analysis
            const compData = await getCompanyAnalysis(selectedCompany);
            setCompanyAnalysis(compData);

            // Get department analyses
            const deptPromises = Object.keys(compData.department_breakdown || {}).map(dept =>
                getDepartmentAnalysis(selectedCompany, dept)
            );
            const deptData = await Promise.all(deptPromises);
            setDepartmentAnalyses(deptData);
        } catch (error) {
            console.error('Error loading analysis:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateReport = async () => {
        if (!selectedCompany) return;

        setGeneratingReport(true);
        try {
            const result = await generateReport(selectedCompany);
            const reportId = result.report.report_id;

            // Download the report
            await downloadReport(reportId);
            alert('Report downloaded successfully!');
        } catch (error) {
            console.error('Error generating report:', error);
            alert('Failed to generate report: ' + (error.response?.data?.detail || error.message));
        } finally {
            setGeneratingReport(false);
        }
    };

    // Prepare chart data
    const classificationData = companyAnalysis ? Object.entries(companyAnalysis.classification_distribution || {}).map(([name, value]) => ({
        name,
        value
    })) : [];

    const departmentData = departmentAnalyses.map(dept => ({
        name: dept.department,
        files: dept.total_files,
        risk: dept.risk_score
    }));

    const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

    const getRiskColor = (score) => {
        if (score < 30) return 'text-green-400 bg-green-400/10';
        if (score < 60) return 'text-orange-400 bg-orange-400/10';
        return 'text-red-400 bg-red-400/10';
    };

    if (!selectedCompany) {
        return (
            <div className="text-center py-12">
                <FileText className="h-16 w-16 text-secondary-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">No Data Available</h2>
                <p className="text-secondary-400">Upload some files first to see analytics</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Analytics Dashboard</h1>
                    <p className="text-secondary-400">Company-wide and department-level insights</p>
                </div>
                <button
                    onClick={handleGenerateReport}
                    disabled={generatingReport}
                    className="btn-primary flex items-center space-x-2"
                >
                    <Download className="h-5 w-5" />
                    <span>{generatingReport ? 'Generating...' : 'Download Report'}</span>
                </button>
            </div>

            {/* Company Selector */}
            <div className="card">
                <label className="block text-sm font-medium text-secondary-300 mb-2">
                    Select Company
                </label>
                <select
                    value={selectedCompany}
                    onChange={(e) => setSelectedCompany(e.target.value)}
                    className="input-field max-w-md"
                >
                    {companies.map(company => (
                        <option key={company} value={company}>{company}</option>
                    ))}
                </select>
            </div>

            {loading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                    <p className="text-secondary-400 mt-4">Loading analytics...</p>
                </div>
            ) : companyAnalysis ? (
                <>
                    {/* Stats Cards */}
                    <div className="grid md:grid-cols-4 gap-6">
                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-secondary-400 mb-1">Total Files</p>
                                    <p className="text-3xl font-bold text-white">{companyAnalysis.total_files}</p>
                                </div>
                                <FileText className="h-10 w-10 text-primary-500" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-secondary-400 mb-1">Departments</p>
                                    <p className="text-3xl font-bold text-white">
                                        {Object.keys(companyAnalysis.department_breakdown || {}).length}
                                    </p>
                                </div>
                                <Users className="h-10 w-10 text-blue-500" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-secondary-400 mb-1">Risk Score</p>
                                    <p className={`text-3xl font-bold ${companyAnalysis.risk_score < 30 ? 'text-green-400' : companyAnalysis.risk_score < 60 ? 'text-orange-400' : 'text-red-400'}`}>
                                        {companyAnalysis.risk_score.toFixed(1)}
                                    </p>
                                </div>
                                <TrendingUp className="h-10 w-10 text-orange-500" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-secondary-400 mb-1">Restricted Files</p>
                                    <p className="text-3xl font-bold text-red-400">
                                        {companyAnalysis.classification_distribution?.Restricted || 0}
                                    </p>
                                </div>
                                <AlertTriangle className="h-10 w-10 text-red-500" />
                            </div>
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Classification Distribution */}
                        <div className="card">
                            <h3 className="text-xl font-semibold text-white mb-4">Classification Distribution</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={classificationData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {classificationData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Department Files */}
                        <div className="card">
                            <h3 className="text-xl font-semibold text-white mb-4">Files by Department</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={departmentData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="name" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                                        labelStyle={{ color: '#e2e8f0' }}
                                    />
                                    <Legend />
                                    <Bar dataKey="files" fill="#0ea5e9" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Department Risk Table */}
                    <div className="card">
                        <h3 className="text-xl font-semibold text-white mb-4">Department Risk Analysis</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-secondary-700">
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-secondary-300">Department</th>
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-secondary-300">Total Files</th>
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-secondary-300">Restricted</th>
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-secondary-300">Confidential</th>
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-secondary-300">Risk Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {departmentAnalyses.map((dept, index) => (
                                        <tr key={index} className="border-b border-secondary-700/50">
                                            <td className="py-3 px-4 text-white font-medium">{dept.department}</td>
                                            <td className="py-3 px-4 text-secondary-300">{dept.total_files}</td>
                                            <td className="py-3 px-4 text-red-400">
                                                {dept.classification_distribution?.Restricted || 0}
                                            </td>
                                            <td className="py-3 px-4 text-orange-400">
                                                {dept.classification_distribution?.Confidential || 0}
                                            </td>
                                            <td className="py-3 px-4">
                                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(dept.risk_score)}`}>
                                                    {dept.risk_score.toFixed(1)}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Top Sensitive Data Types */}
                    {companyAnalysis.top_sensitive_types && companyAnalysis.top_sensitive_types.length > 0 && (
                        <div className="card">
                            <h3 className="text-xl font-semibold text-white mb-4">Most Common Sensitive Data Types</h3>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {companyAnalysis.top_sensitive_types.slice(0, 6).map((item, index) => (
                                    <div key={index} className="bg-secondary-700/50 rounded-lg p-4">
                                        <div className="flex items-center justify-between">
                                            <span className="text-secondary-300">{item.type}</span>
                                            <span className="text-xl font-bold text-primary-400">{item.count}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            ) : null}
        </div>
    );
};

export default Dashboard;
