import { useState, useRef, useEffect } from 'react';
import { Settings, Key, LogOut, ChevronDown, X, Copy, Trash2, Plus } from 'lucide-react';

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
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-slate-700/50 transition-all border border-transparent hover:border-slate-600"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold shadow-lg ring-2 ring-blue-500/20">
          {userInfo.name.charAt(0).toUpperCase()}
        </div>
        <span className="text-sm font-semibold text-white">
          {userInfo.name}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl shadow-2xl border border-slate-700 overflow-hidden z-50 backdrop-blur-xl">
          <div className="px-5 py-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                {userInfo.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="text-base font-bold text-white">{userInfo.name}</p>
                <p className="text-xs text-slate-400">{userInfo.email}</p>
              </div>
            </div>
          </div>

          <div className="py-2">
            <button
              onClick={() => {
                setShowSettings(true);
                setIsOpen(false);
              }}
              className="w-full flex items-center px-5 py-3 text-sm font-medium text-slate-200 hover:text-white hover:bg-gradient-to-r hover:from-blue-600/10 hover:to-purple-600/10 transition-all group"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 group-hover:bg-blue-500/20 flex items-center justify-center mr-3 transition-all">
                <Settings className="w-4 h-4 text-blue-400" />
              </div>
              <span>Account Settings</span>
            </button>

            <button
              onClick={() => {
                setShowApiKeys(true);
                setIsOpen(false);
              }}
              className="w-full flex items-center px-5 py-3 text-sm font-medium text-slate-200 hover:text-white hover:bg-gradient-to-r hover:from-emerald-600/10 hover:to-blue-600/10 transition-all group"
            >
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 group-hover:bg-emerald-500/20 flex items-center justify-center mr-3 transition-all">
                <Key className="w-4 h-4 text-emerald-400" />
              </div>
              <span>API Keys</span>
            </button>
          </div>

          <div className="border-t border-slate-700 bg-slate-900/50">
            <button
              onClick={onLogout}
              className="w-full flex items-center px-5 py-3 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all group"
            >
              <div className="w-8 h-8 rounded-lg bg-red-500/10 group-hover:bg-red-500/20 flex items-center justify-center mr-3 transition-all">
                <LogOut className="w-4 h-4 text-red-400" />
              </div>
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}

      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl max-w-md w-full mx-4 border border-slate-700">
            <div className="flex items-center justify-between p-6 border-b border-slate-700 bg-gradient-to-r from-blue-600/20 to-purple-600/20">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Settings className="w-6 h-6 text-blue-400" />
                  Account Settings
                </h2>
                <p className="text-sm text-slate-400 mt-1">Manage your profile information</p>
              </div>
              <button
                onClick={() => {
                  setShowSettings(false);
                  setEditMode(false);
                  setEditedInfo(userInfo);
                }}
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              <div className="relative">
                <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-blue-500 rounded"></div>
                  Name
                </label>
                <input
                  type="text"
                  value={editMode ? editedInfo.name : userInfo.name}
                  onChange={(e) => setEditedInfo({ ...editedInfo, name: e.target.value })}
                  disabled={!editMode}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  placeholder="Enter your name"
                />
              </div>

              <div className="relative">
                <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-green-500 rounded"></div>
                  Email
                </label>
                <input
                  type="email"
                  value={editMode ? editedInfo.email : userInfo.email}
                  onChange={(e) => setEditedInfo({ ...editedInfo, email: e.target.value })}
                  disabled={!editMode}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  placeholder="your.email@example.com"
                />
              </div>

              <div className="relative">
                <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-purple-500 rounded"></div>
                  Company
                </label>
                <input
                  type="text"
                  value={editMode ? editedInfo.company : userInfo.company}
                  onChange={(e) => setEditedInfo({ ...editedInfo, company: e.target.value })}
                  disabled={!editMode}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  placeholder="Your company name"
                />
              </div>

              {!editMode && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                  <p className="text-sm text-blue-300 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    Click "Edit Information" to update your details
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 p-6 border-t border-slate-700 bg-slate-900/50">
              {editMode ? (
                <>
                  <button
                    onClick={() => {
                      setEditMode(false);
                      setEditedInfo(userInfo);
                    }}
                    className="px-5 py-2.5 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all border border-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveSettings}
                    className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl transition-all shadow-lg shadow-blue-500/50"
                  >
                    Save Changes
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditMode(true)}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl transition-all shadow-lg shadow-blue-500/50"
                >
                  Edit Information
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {showApiKeys && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-slate-700">
            <div className="flex items-center justify-between p-6 border-b border-slate-700 bg-gradient-to-r from-emerald-600/20 to-blue-600/20 sticky top-0 backdrop-blur-sm z-10">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Key className="w-6 h-6 text-emerald-400" />
                  API Keys
                </h2>
                <p className="text-sm text-slate-400 mt-1">Manage your authentication keys</p>
              </div>
              <button
                onClick={() => setShowApiKeys(false)}
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 flex-1 mr-4">
                  <p className="text-sm text-amber-300 flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Keep your API keys secure and never share them publicly
                  </p>
                </div>
                <button
                  onClick={() => setShowNewKeyModal(true)}
                  className="flex items-center px-4 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 rounded-xl transition-all shadow-lg shadow-emerald-500/50"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Key
                </button>
              </div>

              <div className="space-y-4">
                {apiKeys.map((apiKey) => (
                  <div
                    key={apiKey.id}
                    className="p-5 bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-xl hover:border-slate-600 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white text-lg">{apiKey.name}</h3>
                        <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                          </svg>
                          Created {new Date(apiKey.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleCopyKey(apiKey.key)}
                          className="p-2.5 text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 rounded-lg transition-all border border-blue-500/30"
                          title="Copy API key"
                        >
                          {copiedKey === apiKey.key ? (
                            <span className="text-xs font-semibold text-emerald-400">✓ Copied</span>
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDeleteKey(apiKey.id)}
                          className="p-2.5 text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 rounded-lg transition-all border border-red-500/30"
                          title="Delete API key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="bg-slate-950 border border-slate-700 rounded-lg p-4 font-mono text-sm text-emerald-400 break-all relative group">
                      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-blue-500/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
                      <span className="relative">{apiKey.key}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Create New API Key</h2>
              <button
                onClick={() => {
                  setShowNewKeyModal(false);
                  setNewKeyName('');
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Key Name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production Key"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => {
                  setShowNewKeyModal(false);
                  setNewKeyName('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                Create Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
