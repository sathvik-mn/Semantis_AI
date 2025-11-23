import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings, Key, LogOut, ChevronDown, X, Copy, Trash2, Plus, User, Mail, Building2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getCurrentApiKey, generateApiKey, setApiKey, getApiKey, getUserOpenAIKeyStatus, setUserOpenAIKey, removeUserOpenAIKey } from '../api/semanticAPI';

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
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState(false);

  // Use actual user data from AuthContext
  const [userInfo, setUserInfo] = useState({
    email: user?.email || '',
    name: user?.name || user?.email?.split('@')[0] || 'User',
    company: 'My Company'
  });

  // Update userInfo when user changes
  useEffect(() => {
    if (user) {
      setUserInfo({
        email: user.email || '',
        name: user.name || user.email?.split('@')[0] || 'User',
        company: 'My Company'
      });
      setEditedInfo({
        email: user.email || '',
        name: user.name || user.email?.split('@')[0] || 'User',
        company: 'My Company'
      });
    }
  }, [user]);
  const [editMode, setEditMode] = useState(false);
  const [editedInfo, setEditedInfo] = useState(userInfo);
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [generatingKey, setGeneratingKey] = useState(false);
  const [openaiKeyStatus, setOpenaiKeyStatus] = useState<{ key_set: boolean; key_preview?: string } | null>(null);
  const [openaiKeyInput, setOpenaiKeyInput] = useState('');
  const [savingOpenAIKey, setSavingOpenAIKey] = useState(false);
  const [loadingOpenAIStatus, setLoadingOpenAIStatus] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Load API keys from backend
  useEffect(() => {
    const loadApiKeys = async () => {
      if (!user) return;
      
      setLoadingKeys(true);
      try {
        const apiKeyData = await getCurrentApiKey();
        const currentKey = getApiKey();
        
        if (apiKeyData.exists && apiKeyData.api_key) {
          setApiKeys([{
            id: '1',
            key: apiKeyData.api_key,
            name: 'Main API Key',
            created_at: apiKeyData.created_at || new Date().toISOString()
          }]);
        } else if (currentKey) {
          // Fallback to localStorage key
          setApiKeys([{
            id: '1',
            key: currentKey,
            name: 'API Key',
            created_at: new Date().toISOString()
          }]);
        }
      } catch (err) {
        console.error('Failed to load API keys:', err);
        const currentKey = getApiKey();
        if (currentKey) {
          setApiKeys([{
            id: '1',
            key: currentKey,
            name: 'API Key',
            created_at: new Date().toISOString()
          }]);
        }
      } finally {
        setLoadingKeys(false);
      }
    };
    
    if (showApiKeys) {
      loadApiKeys();
    }
  }, [showApiKeys, user]);

  // Load OpenAI key status when settings modal opens
  useEffect(() => {
    const loadOpenAIStatus = async () => {
      if (!user || !showSettings) return;
      
      setLoadingOpenAIStatus(true);
      try {
        const status = await getUserOpenAIKeyStatus();
        setOpenaiKeyStatus(status);
      } catch (err) {
        console.error('Failed to load OpenAI key status:', err);
        setOpenaiKeyStatus({ key_set: false });
      } finally {
        setLoadingOpenAIStatus(false);
      }
    };
    
    loadOpenAIStatus();
  }, [showSettings, user]);

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

  // Handle overlay click to close modals
  const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>, modalType: 'settings' | 'apiKeys' | 'newKey') => {
    if (event.target === event.currentTarget) {
      if (modalType === 'settings') {
        setShowSettings(false);
        setEditMode(false);
        setEditedInfo(userInfo);
      } else if (modalType === 'apiKeys') {
        setShowApiKeys(false);
      } else if (modalType === 'newKey') {
        setShowNewKeyModal(false);
        setNewKeyName('');
      }
    }
  };

  const handleCloseSettings = () => {
    setShowSettings(false);
    setEditMode(false);
    setEditedInfo(userInfo);
  };

  const handleCloseApiKeys = () => {
    setShowApiKeys(false);
  };

  const handleCloseNewKey = () => {
    setShowNewKeyModal(false);
    setNewKeyName('');
  };

  const handleSaveOpenAIKey = async () => {
    if (!openaiKeyInput.trim()) {
      alert('Please enter your OpenAI API key');
      return;
    }

    if (!openaiKeyInput.trim().startsWith('sk-')) {
      alert('Invalid OpenAI API key format. Must start with "sk-"');
      return;
    }

    setSavingOpenAIKey(true);
    try {
      await setUserOpenAIKey(openaiKeyInput.trim());
      setOpenaiKeyInput('');
      // Reload status
      const status = await getUserOpenAIKeyStatus();
      setOpenaiKeyStatus(status);
      alert('OpenAI API key saved successfully!');
    } catch (err: any) {
      alert(err.message || 'Failed to save OpenAI API key');
    } finally {
      setSavingOpenAIKey(false);
    }
  };

  const handleRemoveOpenAIKey = async () => {
    if (!confirm('Are you sure you want to remove your OpenAI API key? You will need to add it again to use the service.')) {
      return;
    }

    setSavingOpenAIKey(true);
    try {
      await removeUserOpenAIKey();
      setOpenaiKeyStatus({ key_set: false });
      alert('OpenAI API key removed successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to remove OpenAI API key');
    } finally {
      setSavingOpenAIKey(false);
    }
  };

  const handleSaveSettings = () => {
    setUserInfo(editedInfo);
    localStorage.setItem('user', JSON.stringify(editedInfo));
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

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      alert('Please enter a name for the API key');
      return;
    }

    setGeneratingKey(true);
    try {
      const result = await generateApiKey({ plan: 'free' });
      const newKey: ApiKeyItem = {
        id: Date.now().toString(),
        key: result.api_key,
        name: newKeyName,
        created_at: result.created_at || new Date().toISOString()
      };

      // Save to localStorage
      setApiKey(result.api_key);
      
      // Update state
      setApiKeys([newKey, ...apiKeys]);
      setNewKeyName('');
      setShowNewKeyModal(false);
    } catch (err: any) {
      alert(err.message || 'Failed to generate API key');
    } finally {
      setGeneratingKey(false);
    }
  };

  return (
    <div style={styles.container} ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          ...styles.triggerButton,
          ...(isOpen ? styles.triggerButtonActive : {}),
        }}
      >
        <div style={styles.avatar}>
          <span style={styles.avatarText}>{userInfo.name.charAt(0).toUpperCase()}</span>
        </div>
        <span style={styles.userName}>{userInfo.name}</span>
        <ChevronDown
          style={{
            ...styles.chevron,
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
          size={16}
        />
      </button>

      {isOpen && (
        <div style={styles.dropdown}>
          <div style={styles.dropdownHeader}>
            <div style={styles.avatarLarge}>
              <span style={styles.avatarLargeText}>{userInfo.name.charAt(0).toUpperCase()}</span>
            </div>
            <div style={styles.userInfoSection}>
              <div style={styles.userNameLarge}>{userInfo.name}</div>
              <div style={styles.userEmail}>{userInfo.email}</div>
              <div style={styles.statusBadge}>
                <div style={styles.statusDot} />
                <span style={styles.statusText}>Connected</span>
              </div>
            </div>
          </div>

          <div style={styles.menuItems}>
            <button
              onClick={() => {
                setShowSettings(true);
                setIsOpen(false);
              }}
              style={styles.menuItem}
            >
              <div style={{...styles.menuIconContainer, ...styles.menuIconContainerBlue}}>
                <Settings size={18} style={styles.menuIcon} />
              </div>
              <span style={styles.menuLabel}>Account Settings</span>
            </button>

            <button
              onClick={() => {
                setShowApiKeys(true);
                setIsOpen(false);
              }}
              style={styles.menuItem}
            >
              <div style={{...styles.menuIconContainer, ...styles.menuIconContainerGreen}}>
                <Key size={18} style={{...styles.menuIcon, color: '#10b981'}} />
              </div>
              <span style={styles.menuLabel}>API Keys</span>
            </button>
          </div>

          <div style={styles.menuFooter}>
            <button
              onClick={onLogout}
              style={styles.logoutButton}
            >
              <div style={styles.logoutIconContainer}>
                <LogOut size={18} style={styles.logoutIcon} />
              </div>
              <span style={styles.logoutLabel}>Sign Out</span>
            </button>
          </div>
        </div>
      )}

      {showSettings && (
        <div 
          style={styles.overlay} 
          onClick={(e) => handleOverlayClick(e, 'settings')}
        >
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div>
                <h2 style={styles.modalTitle}>
                  <Settings size={20} style={{ marginRight: '8px' }} />
                  Account Settings
                </h2>
                <p style={styles.modalSubtitle}>Manage your profile information</p>
              </div>
              <button
                onClick={handleCloseSettings}
                style={styles.closeButton}
              >
                <X size={20} />
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>
                  <User size={14} style={{ marginRight: '6px' }} />
                  Name
                </label>
                <input
                  type="text"
                  value={editMode ? editedInfo.name : userInfo.name}
                  onChange={(e) => setEditedInfo({ ...editedInfo, name: e.target.value })}
                  disabled={!editMode}
                  style={{
                    ...styles.input,
                    opacity: editMode ? 1 : 0.6,
                    cursor: editMode ? 'text' : 'not-allowed',
                  }}
                  placeholder="Enter your name"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>
                  <Mail size={14} style={{ marginRight: '6px' }} />
                  Email
                </label>
                <input
                  type="email"
                  value={editMode ? editedInfo.email : userInfo.email}
                  onChange={(e) => setEditedInfo({ ...editedInfo, email: e.target.value })}
                  disabled={!editMode}
                  style={{
                    ...styles.input,
                    opacity: editMode ? 1 : 0.6,
                    cursor: editMode ? 'text' : 'not-allowed',
                  }}
                  placeholder="your.email@example.com"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>
                  <Building2 size={14} style={{ marginRight: '6px' }} />
                  Company
                </label>
                <input
                  type="text"
                  value={editMode ? editedInfo.company : userInfo.company}
                  onChange={(e) => setEditedInfo({ ...editedInfo, company: e.target.value })}
                  disabled={!editMode}
                  style={{
                    ...styles.input,
                    opacity: editMode ? 1 : 0.6,
                    cursor: editMode ? 'text' : 'not-allowed',
                  }}
                  placeholder="Your company name"
                />
              </div>

              {!editMode && (
                <div style={styles.infoBox}>
                  <svg style={{ width: '16px', height: '16px', flexShrink: 0, marginTop: '2px' }} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <span>Click "Edit Information" to update your details</span>
                </div>
              )}

              <div style={{ ...styles.inputGroup, marginTop: '24px', paddingTop: '24px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <label style={styles.label}>
                  <Key size={14} style={{ marginRight: '6px' }} />
                  OpenAI API Key
                </label>
                {loadingOpenAIStatus ? (
                  <div style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '14px', padding: '8px 0' }}>Loading...</div>
                ) : openaiKeyStatus?.key_set ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <input
                        type="text"
                        value={openaiKeyStatus.key_preview || 'sk-***'}
                        disabled
                        style={{
                          ...styles.input,
                          opacity: 0.6,
                          cursor: 'not-allowed',
                          fontFamily: 'monospace',
                        }}
                      />
                      <button
                        onClick={handleRemoveOpenAIKey}
                        disabled={savingOpenAIKey}
                        style={{
                          ...styles.cancelButton,
                          padding: '8px 16px',
                          fontSize: '13px',
                        }}
                      >
                        {savingOpenAIKey ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                    <div style={styles.infoBox}>
                      <svg style={{ width: '14px', height: '14px', flexShrink: 0, marginTop: '2px' }} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <span style={{ fontSize: '12px' }}>Your OpenAI API key is configured. Your queries are private and use your own OpenAI account.</span>
                    </div>
                  </div>
                ) : (
                  <div>
                    <input
                      type="password"
                      value={openaiKeyInput}
                      onChange={(e) => setOpenaiKeyInput(e.target.value)}
                      placeholder="sk-..."
                      style={{
                        ...styles.input,
                        fontFamily: 'monospace',
                        marginBottom: '8px',
                      }}
                    />
                    <button
                      onClick={handleSaveOpenAIKey}
                      disabled={savingOpenAIKey || !openaiKeyInput.trim()}
                      style={{
                        ...styles.primaryButton,
                        width: '100%',
                        padding: '10px',
                      }}
                    >
                      {savingOpenAIKey ? 'Saving...' : 'Save OpenAI API Key'}
                    </button>
                    <div style={styles.infoBox}>
                      <svg style={{ width: '14px', height: '14px', flexShrink: 0, marginTop: '2px' }} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <span style={{ fontSize: '12px' }}>Add your OpenAI API key for complete privacy. Your queries will only use your own OpenAI account.</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div style={styles.modalFooter}>
              {editMode ? (
                <>
                  <button
                    onClick={() => {
                      setEditMode(false);
                      setEditedInfo(userInfo);
                    }}
                    style={styles.cancelButton}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      handleSaveSettings();
                      setEditMode(false);
                    }}
                    style={styles.primaryButton}
                  >
                    Save Changes
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleCloseSettings}
                    style={styles.cancelButton}
                  >
                    Close
                  </button>
                  <button
                    onClick={() => setEditMode(true)}
                    style={styles.primaryButton}
                  >
                    Edit Information
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {showApiKeys && (
        <div 
          style={styles.overlay} 
          onClick={(e) => handleOverlayClick(e, 'apiKeys')}
        >
          <div style={{...styles.modal, maxWidth: '700px'}} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div>
                <h2 style={styles.modalTitle}>
                  <Key size={20} style={{ marginRight: '8px' }} />
                  API Keys
                </h2>
                <p style={styles.modalSubtitle}>Manage your authentication keys</p>
              </div>
              <button
                onClick={handleCloseApiKeys}
                style={styles.closeButton}
              >
                <X size={20} />
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.apiKeysTopBar}>
                <div style={styles.warningBox}>
                  <svg style={{ width: '16px', height: '16px', flexShrink: 0 }} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Keep your API keys secure and never share them publicly</span>
                </div>
                <button
                  onClick={() => setShowNewKeyModal(true)}
                  style={styles.newKeyButton}
                >
                  <Plus size={16} style={{ marginRight: '6px' }} />
                  New Key
                </button>
              </div>

              <div style={styles.apiKeysList}>
                {loadingKeys ? (
                  <div style={styles.loadingText}>Loading API keys...</div>
                ) : apiKeys.length === 0 ? (
                  <div style={styles.emptyState}>
                    <Key size={32} style={{ opacity: 0.3, marginBottom: '12px' }} />
                    <p style={styles.emptyText}>No API keys found</p>
                    <p style={styles.emptySubtext}>Generate one to start using the API</p>
                  </div>
                ) : (
                  apiKeys.map((apiKey) => (
                  <div key={apiKey.id} style={styles.apiKeyCard}>
                    <div style={styles.apiKeyCardHeader}>
                      <div>
                        <h3 style={styles.apiKeyName}>{apiKey.name}</h3>
                        <p style={styles.apiKeyDate}>
                          Created {new Date(apiKey.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                      <div style={styles.apiKeyActions}>
                        <button
                          onClick={() => handleCopyKey(apiKey.key)}
                          style={styles.actionButton}
                          title="Copy API key"
                        >
                          {copiedKey === apiKey.key ? (
                            <span style={{fontSize: '11px', fontWeight: 'bold'}}>✓ Copied</span>
                          ) : (
                            <Copy size={14} />
                          )}
                        </button>
                        <button
                          onClick={() => handleDeleteKey(apiKey.id)}
                          style={{...styles.actionButton, ...styles.deleteButton}}
                          title="Delete API key"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <div style={styles.apiKeyDisplay}>
                      {apiKey.key}
                    </div>
                  </div>
                  ))
                )}
              </div>
            </div>
            
            <div style={styles.modalFooter}>
              <button
                onClick={handleCloseApiKeys}
                style={styles.primaryButton}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {showNewKeyModal && (
        <div 
          style={styles.overlay} 
          onClick={(e) => handleOverlayClick(e, 'newKey')}
        >
          <div style={{...styles.modal, maxWidth: '450px'}} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Create New API Key</h2>
              <button
                onClick={handleCloseNewKey}
                style={styles.closeButton}
              >
                <X size={20} />
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Key Name</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Key"
                  style={styles.input}
                  autoFocus
                />
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={handleCloseNewKey}
                style={styles.cancelButton}
                disabled={generatingKey}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                disabled={generatingKey}
                style={styles.primaryButton}
              >
                {generatingKey ? 'Generating...' : 'Create Key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
  },
  triggerButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 14px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '10px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  triggerButtonActive: {
    background: 'rgba(255, 255, 255, 0.1)',
    borderColor: 'rgba(59, 130, 246, 0.3)',
  },
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '600',
    fontSize: '14px',
  },
  avatarText: {
    color: '#fff',
  },
  userName: {
    fontSize: '14px',
    fontWeight: '500',
  },
  chevron: {
    color: 'rgba(255, 255, 255, 0.6)',
    transition: 'transform 0.2s ease',
  },
  dropdown: {
    position: 'absolute',
    right: 0,
    top: 'calc(100% + 8px)',
    width: '300px',
    background: 'rgba(0, 0, 0, 0.95)',
    backdropFilter: 'blur(40px)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '16px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6), 0 0 1px rgba(255, 255, 255, 0.1)',
    zIndex: 1000,
    overflow: 'hidden',
    animation: 'dropdownSlideIn 0.2s ease',
  },
  dropdownHeader: {
    padding: '20px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(59, 130, 246, 0.06)',
  },
  avatarLarge: {
    width: '52px',
    height: '52px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '700',
    fontSize: '22px',
    marginBottom: '12px',
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
  },
  avatarLargeText: {
    color: '#fff',
  },
  userInfoSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  userNameLarge: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#fff',
  },
  userEmail: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  statusBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 10px',
    background: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    borderRadius: '6px',
    marginTop: '6px',
    width: 'fit-content',
  },
  statusDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#10b981',
  },
  statusText: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#10b981',
  },
  menuItems: {
    padding: '8px',
  },
  menuItem: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 12px',
    background: 'transparent',
    border: 'none',
    borderRadius: '10px',
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  menuIconContainer: {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
  },
  menuIconContainerBlue: {
    background: 'rgba(59, 130, 246, 0.12)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
  menuIconContainerGreen: {
    background: 'rgba(16, 185, 129, 0.12)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
  },
  menuIcon: {
    color: '#3b82f6',
  },
  menuLabel: {
    flex: 1,
    textAlign: 'left',
  },
  menuFooter: {
    padding: '8px',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(0, 0, 0, 0.3)',
  },
  logoutButton: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 12px',
    background: 'transparent',
    border: 'none',
    borderRadius: '10px',
    color: '#ef4444',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  logoutIconContainer: {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(239, 68, 68, 0.12)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
  },
  logoutIcon: {
    color: '#ef4444',
  },
  logoutLabel: {
    flex: 1,
    textAlign: 'left',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.75)',
    backdropFilter: 'blur(8px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000,
    padding: '20px',
    animation: 'fadeIn 0.2s ease',
  },
  modal: {
    width: '100%',
    maxWidth: '500px',
    maxHeight: '90vh',
    background: 'rgba(0, 0, 0, 0.95)',
    backdropFilter: 'blur(40px)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '20px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    animation: 'modalSlideUp 0.3s ease',
  },
  modalHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    padding: '24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(59, 130, 246, 0.06)',
  },
  modalTitle: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    marginBottom: '4px',
  },
  modalSubtitle: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  closeButton: {
    padding: '8px',
    background: 'transparent',
    border: 'none',
    borderRadius: '8px',
    color: 'rgba(255, 255, 255, 0.6)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  modalBody: {
    padding: '24px',
    overflowY: 'auto',
    flex: 1,
  },
  inputGroup: {
    marginBottom: '20px',
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '13px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: '8px',
  },
  input: {
    width: '100%',
    padding: '12px 14px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '10px',
    color: '#fff',
    outline: 'none',
    transition: 'all 0.2s ease',
    boxSizing: 'border-box',
  },
  infoBox: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '14px',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '10px',
    color: '#60a5fa',
    fontSize: '13px',
    lineHeight: '1.5',
  },
  modalFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: '12px',
    padding: '20px 24px',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(0, 0, 0, 0.3)',
  },
  cancelButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '10px',
    color: 'rgba(255, 255, 255, 0.8)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  primaryButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
  },
  apiKeysTopBar: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    marginBottom: '20px',
    flexWrap: 'wrap',
  },
  warningBox: {
    flex: 1,
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '12px 14px',
    background: 'rgba(251, 191, 36, 0.1)',
    border: '1px solid rgba(251, 191, 36, 0.2)',
    borderRadius: '10px',
    color: '#fbbf24',
    fontSize: '12px',
    lineHeight: '1.4',
    minWidth: '200px',
  },
  newKeyButton: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 18px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
    flexShrink: 0,
  },
  apiKeysList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  apiKeyCard: {
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    transition: 'all 0.2s ease',
  },
  apiKeyCardHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: '12px',
  },
  apiKeyName: {
    fontSize: '15px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '4px',
  },
  apiKeyDate: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  apiKeyActions: {
    display: 'flex',
    gap: '8px',
  },
  actionButton: {
    padding: '8px 10px',
    background: 'rgba(59, 130, 246, 0.12)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '8px',
    color: '#3b82f6',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteButton: {
    background: 'rgba(239, 68, 68, 0.12)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
    color: '#ef4444',
  },
  apiKeyDisplay: {
    padding: '12px 14px',
    background: 'rgba(0, 0, 0, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '10px',
    fontFamily: 'monospace',
    fontSize: '13px',
    color: '#10b981',
    wordBreak: 'break-all',
  },
  loadingText: {
    textAlign: 'center',
    padding: '40px',
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: '14px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    textAlign: 'center',
  },
  emptyText: {
    fontSize: '16px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '8px',
  },
  emptySubtext: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
};
