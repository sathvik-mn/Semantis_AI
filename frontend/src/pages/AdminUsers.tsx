import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Search, MoreVertical, X, Key, Shield, Building2, Activity,
  ChevronDown, AlertTriangle, CheckCircle, XCircle,
  FileText, Users, Zap, DollarSign, Hash, Globe
} from 'lucide-react';
import { adminAPI, User } from '../api/adminAPI';
import { format, formatDistanceToNow } from 'date-fns';

// ── Types ──────────────────────────────────────────────────────────────────────

interface UserDetails {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  company: string;
  created_at: string;
  updated_at: string | null;
  api_keys: Array<{
    id: number;
    api_key: string;
    tenant_id: string;
    plan: string;
    is_active: boolean;
    scope: string;
    label: string;
    usage_count: number;
    created_at: string;
    last_used_at: string | null;
    expires_at: string | null;
  }>;
  organizations: Array<{
    org_id: string;
    org_name: string;
    slug: string;
    org_plan: string;
    role: string;
  }>;
  usage_stats_30d: {
    total_requests: number;
    total_hits: number;
    total_misses: number;
    total_tokens: number;
    total_cost: number;
  };
  recent_activity: Array<{
    endpoint: string;
    requests: number;
    hits: number;
    misses: number;
    cost: number;
  }>;
  audit_logs: Array<{
    id: number;
    action: string;
    resource_type: string;
    resource_id: string;
    details: any;
    created_at: string;
  }>;
}

interface Toast {
  id: number;
  type: 'success' | 'error';
  message: string;
}

// ── Plan & Status Helpers ──────────────────────────────────────────────────────

const PLANS = ['free', 'pro', 'team', 'enterprise'] as const;

const planColors: Record<string, string> = {
  free: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  pro: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  team: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  enterprise: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
};

function PlanBadge({ plan }: { plan: string }) {
  const color = planColors[plan] || planColors.free;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${color}`}>
      {plan}
    </span>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return active ? (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">
      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
      Active
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">
      <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
      Inactive
    </span>
  );
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    owner: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    admin: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    member: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${colors[role] || colors.member}`}>
      {role}
    </span>
  );
}

// ── Toast Container ────────────────────────────────────────────────────────────

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
            t.type === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}
        >
          {t.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <XCircle className="w-4 h-4 shrink-0" />}
          <span className="flex-1">{t.message}</span>
          <button type="button" onClick={() => onDismiss(t.id)} className="ml-2 hover:opacity-80" aria-label="Dismiss notification">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Confirmation Dialog ────────────────────────────────────────────────────────

function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
  loading,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]" onClick={onCancel}>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Details Modal ──────────────────────────────────────────────────────────────

function DetailsModal({
  user,
  onClose,
}: {
  user: UserDetails;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'overview' | 'keys' | 'activity' | 'audit'>('overview');
  const stats = user.usage_stats_30d;

  const tabs = [
    { id: 'overview' as const, label: 'Overview' },
    { id: 'keys' as const, label: `API Keys (${user.api_keys?.length ?? 0})` },
    { id: 'activity' as const, label: 'Activity' },
    { id: 'audit' as const, label: 'Audit Log' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-start justify-between shrink-0">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {user.name || 'Unnamed User'}
              </h2>
              {user.is_admin && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">
                  <Shield className="w-3 h-3" />
                  Admin
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{user.email}</p>
            {user.company && (
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5">
                <Building2 className="w-3.5 h-3.5" />
                {user.company}
              </p>
            )}
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Joined {user.created_at ? format(new Date(user.created_at), 'MMMM d, yyyy') : 'N/A'}
              {user.updated_at && ` · Updated ${formatDistanceToNow(new Date(user.updated_at), { addSuffix: true })}`}
            </p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1" aria-label="Close details">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 shrink-0">
          <nav className="flex gap-6 -mb-px">
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* ── Overview Tab ── */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Usage Stats 30d */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
                  Usage Stats (30 days)
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  <StatCard icon={<Activity className="w-4 h-4" />} label="Requests" value={stats?.total_requests ?? 0} color="blue" />
                  <StatCard icon={<CheckCircle className="w-4 h-4" />} label="Cache Hits" value={stats?.total_hits ?? 0} color="green" />
                  <StatCard icon={<XCircle className="w-4 h-4" />} label="Cache Misses" value={stats?.total_misses ?? 0} color="red" />
                  <StatCard icon={<Hash className="w-4 h-4" />} label="Tokens" value={stats?.total_tokens ?? 0} color="purple" />
                  <StatCard icon={<DollarSign className="w-4 h-4" />} label="Cost" value={`$${(stats?.total_cost ?? 0).toFixed(4)}`} color="amber" />
                </div>
              </div>

              {/* Organizations */}
              {user.organizations && user.organizations.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
                    Organizations
                  </h3>
                  <div className="space-y-2">
                    {user.organizations.map((org) => (
                      <div
                        key={org.org_id}
                        className="flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 rounded-lg px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <Building2 className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{org.org_name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{org.slug}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <PlanBadge plan={org.org_plan} />
                          <RoleBadge role={org.role} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── API Keys Tab ── */}
          {activeTab === 'keys' && (
            <div>
              {(!user.api_keys || user.api_keys.length === 0) ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">No API keys found.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Key</th>
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tenant</th>
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Plan</th>
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Scope</th>
                        <th className="text-right py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Usage</th>
                        <th className="text-left py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Used</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
                      {user.api_keys.map((key) => (
                        <tr key={key.id}>
                          <td className="py-2.5 pr-4">
                            <code className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded font-mono text-gray-700 dark:text-gray-300">
                              {key.api_key}
                            </code>
                            {key.label && (
                              <span className="ml-2 text-xs text-gray-400">{key.label}</span>
                            )}
                          </td>
                          <td className="py-2.5 pr-4">
                            <code className="text-xs text-gray-500 dark:text-gray-400 font-mono">{key.tenant_id}</code>
                          </td>
                          <td className="py-2.5 pr-4"><PlanBadge plan={key.plan} /></td>
                          <td className="py-2.5 pr-4"><StatusBadge active={key.is_active} /></td>
                          <td className="py-2.5 pr-4 text-gray-600 dark:text-gray-400">{key.scope}</td>
                          <td className="py-2.5 pr-4 text-right text-gray-900 dark:text-white font-medium">
                            {key.usage_count.toLocaleString()}
                          </td>
                          <td className="py-2.5 text-gray-500 dark:text-gray-400">
                            {key.last_used_at
                              ? formatDistanceToNow(new Date(key.last_used_at), { addSuffix: true })
                              : 'Never'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── Activity Tab ── */}
          {activeTab === 'activity' && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
                Recent Activity (7 days)
              </h3>
              {(!user.recent_activity || user.recent_activity.length === 0) ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">No recent activity.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Endpoint</th>
                        <th className="text-right py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Requests</th>
                        <th className="text-right py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Hits</th>
                        <th className="text-right py-2 pr-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Misses</th>
                        <th className="text-right py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
                      {user.recent_activity.map((act, i) => (
                        <tr key={i}>
                          <td className="py-2.5 pr-4">
                            <div className="flex items-center gap-2">
                              <Globe className="w-3.5 h-3.5 text-gray-400" />
                              <code className="text-xs font-mono text-gray-700 dark:text-gray-300">{act.endpoint}</code>
                            </div>
                          </td>
                          <td className="py-2.5 pr-4 text-right text-gray-900 dark:text-white">{act.requests.toLocaleString()}</td>
                          <td className="py-2.5 pr-4 text-right text-green-600 dark:text-green-400">{act.hits.toLocaleString()}</td>
                          <td className="py-2.5 pr-4 text-right text-red-600 dark:text-red-400">{act.misses.toLocaleString()}</td>
                          <td className="py-2.5 text-right text-gray-900 dark:text-white">${act.cost.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── Audit Log Tab ── */}
          {activeTab === 'audit' && (
            <div>
              {(!user.audit_logs || user.audit_logs.length === 0) ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">No audit logs found.</p>
              ) : (
                <div className="space-y-2">
                  {user.audit_logs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg px-4 py-3"
                    >
                      <FileText className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">{log.action}</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ''}
                          </span>
                        </div>
                        {log.details && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                            {typeof log.details === 'string' ? log.details : JSON.stringify(log.details)}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap shrink-0">
                        {log.created_at ? formatDistanceToNow(new Date(log.created_at), { addSuffix: true }) : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    red: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
  };
  const c = colorMap[color] || colorMap.blue;
  return (
    <div className={`rounded-lg p-3 ${c}`}>
      <div className="flex items-center gap-1.5 mb-1 opacity-80">{icon}<span className="text-xs font-medium">{label}</span></div>
      <p className="text-lg font-bold">{typeof value === 'number' ? value.toLocaleString() : value}</p>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Details modal
  const [selectedUser, setSelectedUser] = useState<UserDetails | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  // Action menu
  const [actionMenuOpen, setActionMenuOpen] = useState<string | null>(null);
  const [planMenuOpen, setPlanMenuOpen] = useState<string | null>(null);
  const actionMenuRef = useRef<HTMLDivElement>(null);

  // Confirm dialog
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    userId: string;
    userName: string;
    action: 'activate' | 'deactivate';
  }>({ open: false, userId: '', userName: '', action: 'deactivate' });
  const [confirmLoading, setConfirmLoading] = useState(false);

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastIdRef = useRef(0);

  const addToast = useCallback((type: 'success' | 'error', message: string) => {
    const id = ++toastIdRef.current;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Close action menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (actionMenuRef.current && !actionMenuRef.current.contains(e.target as Node)) {
        setActionMenuOpen(null);
        setPlanMenuOpen(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load users
  useEffect(() => {
    loadUsers();
  }, [currentPage, search]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getAllUsers(currentPage, 20, search || undefined);
      setUsers(data.users);
      setTotal(data.total);
      setPages(data.pages);
    } catch (error) {
      console.error('Error loading users:', error);
      addToast('error', 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearch(value);
    setCurrentPage(1);
  };

  const handleViewDetails = async (userId: string) => {
    try {
      setDetailsLoading(true);
      setActionMenuOpen(null);
      setPlanMenuOpen(null);
      const details = await adminAPI.getUserDetails(userId);
      setSelectedUser(details);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Error loading user details:', error);
      addToast('error', 'Failed to load user details.');
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleChangePlan = async (userId: string, plan: string) => {
    try {
      setActionMenuOpen(null);
      setPlanMenuOpen(null);
      await adminAPI.updateUserPlan(userId, plan);
      addToast('success', `Plan updated to "${plan}" successfully.`);
      loadUsers();
    } catch (error) {
      console.error('Error updating plan:', error);
      addToast('error', 'Failed to update user plan.');
    }
  };

  const handleToggleActive = (userId: string, userName: string, currentlyActive: boolean) => {
    setActionMenuOpen(null);
    setPlanMenuOpen(null);
    if (currentlyActive) {
      // Deactivate requires confirmation
      setConfirmDialog({
        open: true,
        userId,
        userName: userName || 'this user',
        action: 'deactivate',
      });
    } else {
      // Activate directly
      doToggleActive(userId, 'activate');
    }
  };

  const doToggleActive = async (userId: string, action: 'activate' | 'deactivate') => {
    try {
      setConfirmLoading(true);
      if (action === 'deactivate') {
        await adminAPI.deactivateUser(userId);
        addToast('success', 'User deactivated successfully.');
      } else {
        await adminAPI.activateUser(userId);
        addToast('success', 'User activated successfully.');
      }
      loadUsers();
    } catch (error) {
      console.error(`Error ${action}ing user:`, error);
      addToast('error', `Failed to ${action} user.`);
    } finally {
      setConfirmLoading(false);
      setConfirmDialog({ open: false, userId: '', userName: '', action: 'deactivate' });
    }
  };

  // ── Render ──

  if (loading && users.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600 dark:text-gray-400">Loading users...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {total} total user{total !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Table Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        {/* Search Bar */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search users by email or name..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  API Keys
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Total Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Last Active
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Joined
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {user.name || 'No name'}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {user.email}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-sm text-gray-900 dark:text-white">
                      <Key className="w-3.5 h-3.5 text-gray-400" />
                      {user.api_key_count}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {(user.total_usage ?? 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {user.last_used_at
                      ? formatDistanceToNow(new Date(user.last_used_at), { addSuffix: true })
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {format(new Date(user.created_at), 'MMM d, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="relative inline-block text-left" ref={actionMenuOpen === user.id ? actionMenuRef : undefined}>
                      <button
                        type="button"
                        onClick={() => {
                          setActionMenuOpen(actionMenuOpen === user.id ? null : user.id);
                          setPlanMenuOpen(null);
                        }}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                        aria-label="User actions"
                      >
                        <MoreVertical className="w-5 h-5" />
                      </button>

                      {actionMenuOpen === user.id && (
                        <div className="origin-top-right absolute right-0 mt-2 w-52 rounded-lg shadow-lg bg-white dark:bg-gray-700 ring-1 ring-black/5 dark:ring-white/10 z-20">
                          <div className="py-1">
                            {/* View Details */}
                            <button
                              type="button"
                              onClick={() => handleViewDetails(user.id)}
                              disabled={detailsLoading}
                              className="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50"
                            >
                              <Users className="w-4 h-4" />
                              {detailsLoading ? 'Loading...' : 'View Details'}
                            </button>

                            {/* Change Plan (submenu) */}
                            <div className="relative">
                              <button
                                type="button"
                                onClick={() => setPlanMenuOpen(planMenuOpen === user.id ? null : user.id)}
                                className="flex items-center justify-between w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                              >
                                <span className="flex items-center gap-2">
                                  <Zap className="w-4 h-4" />
                                  Change Plan
                                </span>
                                <ChevronDown className={`w-4 h-4 transition-transform ${planMenuOpen === user.id ? 'rotate-180' : ''}`} />
                              </button>

                              {planMenuOpen === user.id && (
                                <div className="border-t border-gray-100 dark:border-gray-600 bg-gray-50 dark:bg-gray-750">
                                  {PLANS.map((plan) => (
                                    <button
                                      type="button"
                                      key={plan}
                                      onClick={() => handleChangePlan(user.id, plan)}
                                      className="flex items-center gap-2 w-full text-left px-6 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                                      aria-label={`Change plan to ${plan}`}
                                    >
                                      <PlanBadge plan={plan} />
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Divider */}
                            <div className="border-t border-gray-100 dark:border-gray-600 my-1" />

                            {/* Activate / Deactivate - we show both and let the backend determine state */}
                            <button
                              type="button"
                              onClick={() => handleToggleActive(user.id, user.name, true)}
                              className="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                              <XCircle className="w-4 h-4" />
                              Deactivate User
                            </button>
                            <button
                              type="button"
                              onClick={() => handleToggleActive(user.id, user.name, false)}
                              className="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
                            >
                              <CheckCircle className="w-4 h-4" />
                              Activate User
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {users.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-500 dark:text-gray-400">
                    No users found{search ? ` matching "${search}"` : ''}.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Loading overlay for table refresh */}
        {loading && users.length > 0 && (
          <div className="px-6 py-2 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              Refreshing...
            </div>
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Page {currentPage} of {pages} ({total} users)
            </div>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage(Math.min(pages, currentPage + 1))}
                disabled={currentPage === pages}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedUser && (
        <DetailsModal
          user={selectedUser}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedUser(null);
          }}
        />
      )}

      {/* Confirm Dialog for Deactivation */}
      <ConfirmDialog
        open={confirmDialog.open}
        title="Deactivate User"
        message={`Are you sure you want to deactivate ${confirmDialog.userName}? All their API keys will stop working immediately.`}
        confirmLabel="Deactivate"
        onConfirm={() => doToggleActive(confirmDialog.userId, confirmDialog.action)}
        onCancel={() => setConfirmDialog({ open: false, userId: '', userName: '', action: 'deactivate' })}
        loading={confirmLoading}
      />
    </div>
  );
}
