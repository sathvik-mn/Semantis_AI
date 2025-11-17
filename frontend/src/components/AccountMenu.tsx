import { useState, useRef, useEffect } from 'react';
import { Settings, Key, LogOut, ChevronDown, X, Copy, Trash2, Plus, User, Mail, Building2 } from 'lucide-react';

interface AccountMenuProps {
  onLogout: () => void;
}

interface ApiKeyItem {
  id: string;
  key: string;
  name: string;
  created_at: string;
}

export function AccountMenu({ onLogout }: AccountMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState(false);
  const [userInfo, setUserInfo] = useState({
    email: 'user@example.com',
    name: 'User',
    company: 'My Company'
  });
  const [editMode, setEditMode] = useState(false);
  const [editedInfo, setEditedInfo] = useState(userInfo);
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([
    {
      id: '1',
      key: 'sc-1234567890abcdef',
      name: 'Default Key',
      created_at: new Date().toISOString()
    }
  ]);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSaveSettings = () => {
    setUserInfo(editedInfo);
    setEditMode(false);
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleDeleteKey = (id: string) => {
    if (apiKeys.length === 1) {
      alert('You must have at least one API key');
      return;
    }
    if (confirm('Are you sure you want to delete this API key?')) {
      setApiKeys(apiKeys.filter(k => k.id !== id));
    }
  };

  const handleCreateKey = () => {
    if (!newKeyName.trim()) {
      alert('Please enter a name for the API key');
      return;
    }

    const newKey: ApiKeyItem = {
      id: Date.now().toString(),
      key: `sc-${Math.random().toString(36).substring(2, 18)}`,
      name: newKeyName,
      created_at: new Date().toISOString()
    };

    setApiKeys([...apiKeys, newKey]);
    setNewKeyName('');
    setShowNewKeyModal(false);
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="group relative flex items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-cyan-500/30 transition-all duration-300 shadow-lg hover:shadow-cyan-500/10"
      >
        {/* Avatar with neon glow */}
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 opacity-0 group-hover:opacity-100 blur-md transition-opacity duration-300" />
          <div className="relative w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 via-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-lg ring-2 ring-cyan-400/20 group-hover:ring-cyan-400/40 transition-all duration-300">
            {userInfo.name.charAt(0).toUpperCase()}
          </div>
        </div>

        <span className="text-sm font-semibold text-white/90 group-hover:text-white transition-colors">
          {userInfo.name}
        </span>

        <ChevronDown
          className={`w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-all duration-300 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="relative bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden">
            {/* Neon glow effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-blue-500/5 to-transparent pointer-events-none" />
            <div className="absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />

            {/* Header Section */}
            <div className="relative px-6 py-5 border-b border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-transparent">
              <div className="flex items-center gap-4">
                {/* Large Avatar */}
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 blur-lg opacity-40" />
                  <div className="relative w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 via-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-xl shadow-xl ring-4 ring-cyan-400/20">
                    {userInfo.name.charAt(0).toUpperCase()}
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-bold text-white truncate">{userInfo.name}</h3>
                  <p className="text-sm text-slate-400 truncate">{userInfo.email}</p>
                  <div className="mt-1.5 inline-flex items-center gap-1.5 px-2 py-0.5 bg-cyan-500/10 rounded-md border border-cyan-500/20">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    <span className="text-xs font-medium text-cyan-400">Connected</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <div className="py-2 px-2">
              {/* Account Settings */}
              <button
                onClick={() => {
                  setShowSettings(true);
                  setIsOpen(false);
                }}
                className="group w-full flex items-center gap-4 px-4 py-3.5 text-sm font-medium text-slate-300 hover:text-white rounded-xl hover:bg-gradient-to-r hover:from-cyan-500/10 hover:to-blue-500/10 transition-all duration-300 relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 to-blue-500/0 group-hover:from-cyan-500/5 group-hover:to-blue-500/5 transition-all duration-300" />
                <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/10 to-blue-500/10 group-hover:from-cyan-500/20 group-hover:to-blue-500/20 border border-cyan-500/20 group-hover:border-cyan-400/40 transition-all duration-300 shadow-lg group-hover:shadow-cyan-500/20">
                  <Settings className="w-5 h-5 text-cyan-400" />
                </div>
                <span className="relative">Account Settings</span>
                <div className="relative ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronDown className="w-4 h-4 -rotate-90 text-cyan-400" />
                </div>
              </button>

              {/* API Keys */}
              <button
                onClick={() => {
                  setShowApiKeys(true);
                  setIsOpen(false);
                }}
                className="group w-full flex items-center gap-4 px-4 py-3.5 text-sm font-medium text-slate-300 hover:text-white rounded-xl hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-purple-500/10 transition-all duration-300 relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:to-purple-500/5 transition-all duration-300" />
                <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 group-hover:from-blue-500/20 group-hover:to-purple-500/20 border border-blue-500/20 group-hover:border-blue-400/40 transition-all duration-300 shadow-lg group-hover:shadow-blue-500/20">
                  <Key className="w-5 h-5 text-blue-400" />
                </div>
                <span className="relative">API Keys</span>
                <div className="relative ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronDown className="w-4 h-4 -rotate-90 text-blue-400" />
                </div>
              </button>
            </div>

            {/* Sign Out Section */}
            <div className="border-t border-slate-700/50 p-2 bg-slate-900/50">
              <button
                onClick={onLogout}
                className="group w-full flex items-center gap-4 px-4 py-3.5 text-sm font-medium text-red-400 hover:text-red-300 rounded-xl hover:bg-red-500/10 transition-all duration-300 relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-red-500/0 group-hover:bg-red-500/5 transition-all duration-300" />
                <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/10 group-hover:bg-red-500/20 border border-red-500/20 group-hover:border-red-400/40 transition-all duration-300">
                  <LogOut className="w-5 h-5 text-red-400" />
                </div>
                <span className="relative">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Account Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="relative bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-lg w-full border border-slate-700/50 animate-in zoom-in-95 duration-200">
            {/* Neon border glow */}
            <div className="absolute -inset-px bg-gradient-to-br from-cyan-500/20 via-blue-500/20 to-purple-500/20 rounded-2xl blur-xl" />

            {/* Modal content */}
            <div className="relative">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-transparent">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
                      <Settings className="w-5 h-5 text-cyan-400" />
                    </div>
                    Account Settings
                  </h2>
                  <p className="text-sm text-slate-400 mt-1.5 ml-13">Manage your profile information</p>
                </div>
                <button
                  onClick={() => {
                    setShowSettings(false);
                    setEditMode(false);
                    setEditedInfo(userInfo);
                  }}
                  className="group p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all duration-200 border border-transparent hover:border-slate-700"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <div className="p-6 space-y-5">
                {/* Name Field */}
                <div className="relative group">
                  <label className="block text-sm font-semibold text-slate-300 mb-2.5 flex items-center gap-2">
                    <User className="w-4 h-4 text-cyan-400" />
                    Name
                  </label>
                  <input
                    type="text"
                    value={editMode ? editedInfo.name : userInfo.name}
                    onChange={(e) => setEditedInfo({ ...editedInfo, name: e.target.value })}
                    disabled={!editMode}
                    className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 placeholder:text-slate-500"
                    placeholder="Enter your name"
                  />
                </div>

                {/* Email Field */}
                <div className="relative group">
                  <label className="block text-sm font-semibold text-slate-300 mb-2.5 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={editMode ? editedInfo.email : userInfo.email}
                    onChange={(e) => setEditedInfo({ ...editedInfo, email: e.target.value })}
                    disabled={!editMode}
                    className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 placeholder:text-slate-500"
                    placeholder="your.email@example.com"
                  />
                </div>

                {/* Company Field */}
                <div className="relative group">
                  <label className="block text-sm font-semibold text-slate-300 mb-2.5 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-purple-400" />
                    Company
                  </label>
                  <input
                    type="text"
                    value={editMode ? editedInfo.company : userInfo.company}
                    onChange={(e) => setEditedInfo({ ...editedInfo, company: e.target.value })}
                    disabled={!editMode}
                    className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 placeholder:text-slate-500"
                    placeholder="Your company name"
                  />
                </div>

                {/* Info Box */}
                {!editMode && (
                  <div className="relative bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-xl p-4 overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-blue-500/5" />
                    <p className="relative text-sm text-cyan-300 flex items-start gap-3">
                      <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      Click "Edit Information" to update your details
                    </p>
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="flex justify-end gap-3 px-6 py-5 border-t border-slate-700/50 bg-slate-900/50">
                {editMode ? (
                  <>
                    <button
                      onClick={() => {
                        setEditMode(false);
                        setEditedInfo(userInfo);
                      }}
                      className="px-6 py-3 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all duration-200 border border-slate-700"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveSettings}
                      className="relative px-6 py-3 text-sm font-semibold text-white rounded-xl transition-all duration-200 overflow-hidden group"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500" />
                      <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                      <div className="absolute inset-0 shadow-lg shadow-cyan-500/50 group-hover:shadow-cyan-500/70 transition-all duration-200" />
                      <span className="relative">Save Changes</span>
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setEditMode(true)}
                    className="relative px-6 py-3 text-sm font-semibold text-white rounded-xl transition-all duration-200 overflow-hidden group"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500" />
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                    <div className="absolute inset-0 shadow-lg shadow-cyan-500/50 group-hover:shadow-cyan-500/70 transition-all duration-200" />
                    <span className="relative">Edit Information</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* API Keys Modal */}
      {showApiKeys && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="relative bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden border border-slate-700/50 animate-in zoom-in-95 duration-200">
            {/* Neon border glow */}
            <div className="absolute -inset-px bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-cyan-500/20 rounded-2xl blur-xl" />

            {/* Modal content */}
            <div className="relative flex flex-col h-full max-h-[85vh]">
              {/* Header */}
              <div className="flex-shrink-0 flex items-center justify-between px-6 py-5 border-b border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-transparent">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30">
                      <Key className="w-5 h-5 text-blue-400" />
                    </div>
                    API Keys
                  </h2>
                  <p className="text-sm text-slate-400 mt-1.5 ml-13">Manage your authentication keys</p>
                </div>
                <button
                  onClick={() => setShowApiKeys(false)}
                  className="group p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all duration-200 border border-transparent hover:border-slate-700"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* Warning + New Key Button */}
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center mb-6">
                  <div className="flex-1 relative bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-xl p-4 overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-orange-500/5" />
                    <p className="relative text-sm text-amber-300 flex items-start gap-3">
                      <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      Keep your API keys secure and never share them publicly
                    </p>
                  </div>
                  <button
                    onClick={() => setShowNewKeyModal(true)}
                    className="relative flex items-center gap-2 px-5 py-3 text-sm font-semibold text-white rounded-xl transition-all duration-200 overflow-hidden group flex-shrink-0"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500" />
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                    <div className="absolute inset-0 shadow-lg shadow-blue-500/50 group-hover:shadow-blue-500/70 transition-all duration-200" />
                    <Plus className="relative w-4 h-4" />
                    <span className="relative">New Key</span>
                  </button>
                </div>

                {/* API Keys List */}
                <div className="space-y-4">
                  {apiKeys.map((apiKey) => (
                    <div
                      key={apiKey.id}
                      className="relative group bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 hover:border-slate-600/50 transition-all duration-200 overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:to-purple-500/5 transition-all duration-200" />

                      <div className="relative flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="font-bold text-white text-lg mb-1">{apiKey.name}</h3>
                          <p className="text-xs text-slate-400 flex items-center gap-2">
                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                            </svg>
                            Created {new Date(apiKey.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCopyKey(apiKey.key)}
                            className="relative p-2.5 rounded-lg transition-all duration-200 overflow-hidden group/btn"
                            title="Copy API key"
                          >
                            <div className="absolute inset-0 bg-blue-500/10 group-hover/btn:bg-blue-500/20" />
                            <div className="absolute inset-0 border border-blue-500/30 group-hover/btn:border-blue-500/50 rounded-lg" />
                            {copiedKey === apiKey.key ? (
                              <span className="relative text-xs font-bold text-emerald-400">✓</span>
                            ) : (
                              <Copy className="relative w-4 h-4 text-blue-400" />
                            )}
                          </button>
                          <button
                            onClick={() => handleDeleteKey(apiKey.id)}
                            className="relative p-2.5 rounded-lg transition-all duration-200 overflow-hidden group/btn"
                            title="Delete API key"
                          >
                            <div className="absolute inset-0 bg-red-500/10 group-hover/btn:bg-red-500/20" />
                            <div className="absolute inset-0 border border-red-500/30 group-hover/btn:border-red-500/50 rounded-lg" />
                            <Trash2 className="relative w-4 h-4 text-red-400" />
                          </button>
                        </div>
                      </div>

                      <div className="relative bg-slate-950/80 border border-slate-700/50 rounded-lg p-4 font-mono text-sm text-blue-400 break-all overflow-hidden group/code">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-hover/code:opacity-100 transition-opacity duration-200" />
                        <span className="relative">{apiKey.key}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="relative bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-md w-full border border-slate-700/50 animate-in zoom-in-95 duration-200">
            {/* Neon border glow */}
            <div className="absolute -inset-px bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl blur-xl" />

            {/* Modal content */}
            <div className="relative">
              <div className="flex items-center justify-between px-6 py-5 border-b border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-transparent">
                <h2 className="text-xl font-bold text-white">Create New API Key</h2>
                <button
                  onClick={() => {
                    setShowNewKeyModal(false);
                    setNewKeyName('');
                  }}
                  className="group p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all duration-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6">
                <label className="block text-sm font-semibold text-slate-300 mb-2.5">
                  Key Name
                </label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Key"
                  className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 placeholder:text-slate-500"
                  autoFocus
                />
              </div>

              <div className="flex justify-end gap-3 px-6 py-5 border-t border-slate-700/50 bg-slate-900/50">
                <button
                  onClick={() => {
                    setShowNewKeyModal(false);
                    setNewKeyName('');
                  }}
                  className="px-5 py-2.5 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all duration-200 border border-slate-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateKey}
                  className="relative px-5 py-2.5 text-sm font-semibold text-white rounded-xl transition-all duration-200 overflow-hidden group"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500" />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                  <div className="absolute inset-0 shadow-lg shadow-blue-500/50 group-hover:shadow-blue-500/70 transition-all duration-200" />
                  <span className="relative">Create Key</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
