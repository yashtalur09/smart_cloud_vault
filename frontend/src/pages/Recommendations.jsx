import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, Lightbulb, Shield } from 'lucide-react';
import { getRecommendations, generateRecommendations, listCompanies } from '../services/api';

const Recommendations = () => {
    const [companies, setCompanies] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState('');
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [filterPriority, setFilterPriority] = useState('all');

    useEffect(() => {
        loadCompanies();
    }, []);

    useEffect(() => {
        if (selectedCompany) {
            loadRecommendations();
        }
    }, [selectedCompany, filterPriority]);

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

    const loadRecommendations = async () => {
        if (!selectedCompany) return;

        setLoading(true);
        try {
            const priority = filterPriority === 'all' ? null : filterPriority;
            const data = await getRecommendations(selectedCompany, null, priority);
            setRecommendations(data.recommendations || []);
        } catch (error) {
            console.error('Error loading recommendations:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        if (!selectedCompany) return;

        setGenerating(true);
        try {
            await generateRecommendations(selectedCompany);
            await loadRecommendations();
            alert('Recommendations generated successfully!');
        } catch (error) {
            console.error('Error generating recommendations:', error);
            alert('Failed to generate recommendations: ' + (error.response?.data?.detail || error.message));
        } finally {
            setGenerating(false);
        }
    };

    const getPriorityIcon = (priority) => {
        switch (priority) {
            case 'High':
                return <AlertTriangle className="h-5 w-5 text-red-400" />;
            case 'Medium':
                return <AlertCircle className="h-5 w-5 text-orange-400" />;
            case 'Low':
                return <Lightbulb className="h-5 w-5 text-blue-400" />;
            default:
                return <CheckCircle className="h-5 w-5 text-gray-400" />;
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'High':
                return 'border-red-400/30 bg-red-400/10';
            case 'Medium':
                return 'border-orange-400/30 bg-orange-400/10';
            case 'Low':
                return 'border-blue-400/30 bg-blue-400/10';
            default:
                return 'border-gray-400/30 bg-gray-400/10';
        }
    };

    const getPriorityTextColor = (priority) => {
        switch (priority) {
            case 'High':
                return 'text-red-400';
            case 'Medium':
                return 'text-orange-400';
            case 'Low':
                return 'text-blue-400';
            default:
                return 'text-gray-400';
        }
    };

    if (!selectedCompany) {
        return (
            <div className="text-center py-12">
                <Shield className="h-16 w-16 text-secondary-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">No Data Available</h2>
                <p className="text-secondary-400">Upload and analyze files first to get recommendations</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Security Recommendations</h1>
                    <p className="text-secondary-400">AI-powered policy recommendations based on your data analysis</p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="btn-primary flex items-center space-x-2"
                >
                    <Shield className="h-5 w-5" />
                    <span>{generating ? 'Generating...' : 'Generate New'}</span>
                </button>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="grid md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-secondary-300 mb-2">
                            Company
                        </label>
                        <select
                            value={selectedCompany}
                            onChange={(e) => setSelectedCompany(e.target.value)}
                            className="input-field"
                        >
                            {companies.map(company => (
                                <option key={company} value={company}>{company}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-secondary-300 mb-2">
                            Priority Filter
                        </label>
                        <select
                            value={filterPriority}
                            onChange={(e) => setFilterPriority(e.target.value)}
                            className="input-field"
                        >
                            <option value="all">All Priorities</option>
                            <option value="High">High Priority</option>
                            <option value="Medium">Medium Priority</option>
                            <option value="Low">Low Priority</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid md:grid-cols-3 gap-6">
                <div className="card text-center">
                    <AlertTriangle className="h-10 w-10 text-red-400 mx-auto mb-2" />
                    <p className="text-3xl font-bold text-white">
                        {recommendations.filter(r => r.priority === 'High').length}
                    </p>
                    <p className="text-sm text-secondary-400">High Priority</p>
                </div>
                <div className="card text-center">
                    <AlertCircle className="h-10 w-10 text-orange-400 mx-auto mb-2" />
                    <p className="text-3xl font-bold text-white">
                        {recommendations.filter(r => r.priority === 'Medium').length}
                    </p>
                    <p className="text-sm text-secondary-400">Medium Priority</p>
                </div>
                <div className="card text-center">
                    <Lightbulb className="h-10 w-10 text-blue-400 mx-auto mb-2" />
                    <p className="text-3xl font-bold text-white">
                        {recommendations.filter(r => r.priority === 'Low').length}
                    </p>
                    <p className="text-sm text-secondary-400">Low Priority</p>
                </div>
            </div>

            {/* Recommendations List */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                    <p className="text-secondary-400 mt-4">Loading recommendations...</p>
                </div>
            ) : recommendations.length > 0 ? (
                <div className="space-y-4">
                    {recommendations.map((rec, index) => (
                        <div
                            key={rec.id}
                            className={`card border-l-4 ${getPriorityColor(rec.priority)}`}
                        >
                            <div className="flex items-start space-x-4">
                                <div className="flex-shrink-0 mt-1">
                                    {getPriorityIcon(rec.priority)}
                                </div>

                                <div className="flex-1">
                                    <div className="flex items-start justify-between mb-3">
                                        <div>
                                            <h3 className="text-xl font-semibold text-white mb-1">
                                                {index + 1}. {rec.title}
                                            </h3>
                                            <span className={`text-sm font-semibold ${getPriorityTextColor(rec.priority)}`}>
                                                Priority: {rec.priority}
                                            </span>
                                            {rec.department && (
                                                <span className="ml-3 text-sm text-secondary-400">
                                                    Department: {rec.department}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <p className="text-secondary-300 mb-4">{rec.description}</p>

                                    <div className="bg-secondary-700/50 rounded-lg p-4 mb-4">
                                        <h4 className="text-sm font-semibold text-secondary-300 mb-2">Rationale</h4>
                                        <p className="text-sm text-secondary-400">{rec.rationale}</p>
                                    </div>

                                    <div>
                                        <h4 className="text-sm font-semibold text-secondary-300 mb-2">Recommended Actions</h4>
                                        <ul className="space-y-2">
                                            {rec.action_items.map((action, idx) => (
                                                <li key={idx} className="flex items-start space-x-2">
                                                    <CheckCircle className="h-4 w-4 text-primary-400 flex-shrink-0 mt-0.5" />
                                                    <span className="text-sm text-secondary-300">{action}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card text-center py-12">
                    <Shield className="h-16 w-16 text-secondary-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No Recommendations Yet</h3>
                    <p className="text-secondary-400 mb-4">
                        Click "Generate New" to create security policy recommendations
                    </p>
                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="btn-primary inline-flex items-center space-x-2"
                    >
                        <Shield className="h-5 w-5" />
                        <span>{generating ? 'Generating...' : 'Generate Recommendations'}</span>
                    </button>
                </div>
            )}
        </div>
    );
};

export default Recommendations;
