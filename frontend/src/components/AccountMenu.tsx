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
              onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.menuItemHover)}
              onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.menuItem)}
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
              onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.menuItemHover)}
              onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.menuItem)}
            >
              <div style={{...styles.menuIconContainer, ...styles.menuIconContainerGreen}}>
                <Key size={18} style={styles.menuIcon} />
              </div>
              <span style={styles.menuLabel}>API Keys</span>
            </button>
          </div>

          <div style={styles.menuFooter}>
            <button
              onClick={onLogout}
              style={styles.logoutButton}
              onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.logoutButtonHover)}
              onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.logoutButton)}
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
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <div style={styles.modalHeader}>
              <div>
                <h2 style={styles.modalTitle}>
                  <Settings size={20} style={{ marginRight: '8px' }} />
                  Account Settings
                </h2>
                <p style={styles.modalSubtitle}>Manage your profile information</p>
              </div>
              <button
                onClick={() => {
                  setShowSettings(false);
                  setEditMode(false);
                  setEditedInfo(userInfo);
                }}
                style={styles.closeButton}
                onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.closeButtonHover)}
                onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.closeButton)}
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
                    onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.cancelButtonHover)}
                    onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.cancelButton)}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveSettings}
                    style={styles.primaryButton}
                    onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
                    onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
                  >
                    Save Changes
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditMode(true)}
                  style={styles.primaryButton}
                  onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
                  onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
                >
                  Edit Information
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {showApiKeys && (
        <div style={styles.overlay}>
          <div style={{...styles.modal, maxWidth: '700px'}}>
            <div style={styles.modalHeader}>
              <div>
                <h2 style={styles.modalTitle}>
                  <Key size={20} style={{ marginRight: '8px' }} />
                  API Keys
                </h2>
                <p style={styles.modalSubtitle}>Manage your authentication keys</p>
              </div>
              <button
                onClick={() => setShowApiKeys(false)}
                style={styles.closeButton}
                onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.closeButtonHover)}
                onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.closeButton)}
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
                  onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
                  onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
                >
                  <Plus size={16} style={{ marginRight: '6px' }} />
                  New Key
                </button>
              </div>

              <div style={styles.apiKeysList}>
                {apiKeys.map((apiKey) => (
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
                          onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.actionButtonHover)}
                          onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.actionButton)}
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
                          onMouseOver={(e) => Object.assign(e.currentTarget.style, {...styles.actionButton, ...styles.deleteButtonHover})}
                          onMouseOut={(e) => Object.assign(e.currentTarget.style, {...styles.actionButton, ...styles.deleteButton})}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <div style={styles.apiKeyDisplay}>
                      {apiKey.key}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {showNewKeyModal && (
        <div style={styles.overlay}>
          <div style={{...styles.modal, maxWidth: '450px'}}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Create New API Key</h2>
              <button
                onClick={() => {
                  setShowNewKeyModal(false);
                  setNewKeyName('');
                }}
                style={styles.closeButton}
                onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.closeButtonHover)}
                onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.closeButton)}
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
                onClick={() => {
                  setShowNewKeyModal(false);
                  setNewKeyName('');
                }}
                style={styles.cancelButton}
                onMouseOver={(e) => Object.assign(e.currentTarget.style, styles.cancelButtonHover)}
                onMouseOut={(e) => Object.assign(e.currentTarget.style, styles.cancelButton)}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                style={styles.primaryButton}
                onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
                onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
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
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s',
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
    transition: 'transform 0.2s',
  },
  dropdown: {
    position: 'absolute',
    right: 0,
    top: 'calc(100% + 8px)',
    width: '300px',
    background: 'rgba(0, 0, 0, 0.9)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    zIndex: 1000,
    overflow: 'hidden',
  },
  dropdownHeader: {
    padding: '20px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(59, 130, 246, 0.1)',
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
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
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
    animation: 'pulse 2s infinite',
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
    borderRadius: '8px',
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  menuItemHover: {
    background: 'rgba(255, 255, 255, 0.05)',
    color: '#fff',
  },
  menuIconContainer: {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
  },
  menuIconContainerBlue: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
  menuIconContainerGreen: {
    background: 'rgba(16, 185, 129, 0.1)',
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
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
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
    borderRadius: '8px',
    color: '#ef4444',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  logoutButtonHover: {
    background: 'rgba(239, 68, 68, 0.1)',
  },
  logoutIconContainer: {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(239, 68, 68, 0.1)',
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
    background: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(4px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000,
    padding: '20px',
  },
  modal: {
    width: '100%',
    maxWidth: '500px',
    maxHeight: '90vh',
    background: 'rgba(0, 0, 0, 0.95)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  modalHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    padding: '24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(59, 130, 246, 0.05)',
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
    borderRadius: '6px',
    color: 'rgba(255, 255, 255, 0.6)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  closeButtonHover: {
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#fff',
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
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '8px',
  },
  input: {
    width: '100%',
    padding: '12px 14px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    outline: 'none',
    transition: 'all 0.2s',
  },
  infoBox: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '14px',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '8px',
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
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(0, 0, 0, 0.3)',
  },
  cancelButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: 'rgba(255, 255, 255, 0.8)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  cancelButtonHover: {
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#fff',
  },
  primaryButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
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
    borderRadius: '8px',
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
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
    flexShrink: 0,
  },
  apiKeysList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  apiKeyCard: {
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '10px',
    transition: 'all 0.2s',
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
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '6px',
    color: '#3b82f6',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonHover: {
    background: 'rgba(59, 130, 246, 0.2)',
    borderColor: 'rgba(59, 130, 246, 0.4)',
  },
  deleteButton: {
    background: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
    color: '#ef4444',
  },
  deleteButtonHover: {
    background: 'rgba(239, 68, 68, 0.2)',
    borderColor: 'rgba(239, 68, 68, 0.4)',
  },
  apiKeyDisplay: {
    padding: '12px 14px',
    background: 'rgba(0, 0, 0, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    fontFamily: 'monospace',
    fontSize: '13px',
    color: '#10b981',
    wordBreak: 'break-all',
  },
};
