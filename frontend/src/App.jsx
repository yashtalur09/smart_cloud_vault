import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Shield, BarChart3, FileText, Download as DownloadIcon } from 'lucide-react';
import './index.css';

// Pages
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import DownloadRoleBased from './pages/DownloadRoleBased';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-secondary-900 via-secondary-800 to-secondary-900">
        {/* Navigation */}
        <nav className="bg-secondary-800/50 backdrop-blur-lg border-b border-secondary-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <Shield className="h-8 w-8 text-primary-500" />
                <span className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                  SmartCloud Vault
                </span>
              </div>

              <div className="flex space-x-4">
                <Link
                  to="/"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-secondary-300 hover:text-white hover:bg-secondary-700 transition-all"
                >
                  <FileText className="h-5 w-5" />
                  <span>Upload</span>
                </Link>
                <Link
                  to="/download-role"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-secondary-300 hover:text-white hover:bg-secondary-700 transition-all"
                >
                  <DownloadIcon className="h-5 w-5" />
                  <span>Download</span>
                </Link>
                <Link
                  to="/dashboard"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-secondary-300 hover:text-white hover:bg-secondary-700 transition-all"
                >
                  <BarChart3 className="h-5 w-5" />
                  <span>Dashboard</span>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/download-role" element={<DownloadRoleBased />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="mt-16 border-t border-secondary-700 bg-secondary-800/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-secondary-400 text-sm">
              © 2024 SmartCloud Vault - Sensitive Data Protection Platform
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
