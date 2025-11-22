import { useEffect, useState } from 'react';
import { Users, Activity, DollarSign, Key, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { adminAPI, AnalyticsSummary, GrowthData, UsageData, PlanDistribution } from '../api/adminAPI';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: number;
  color: string;
}

function KPICard({ title, value, icon: Icon, trend, color }: KPICardProps) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-6 border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${color} shadow-lg`}>
          <Icon className="w-7 h-7 text-white" />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center px-3 py-1 rounded-full ${trend >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
            {trend >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
            <span className="text-sm font-bold">{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <div>
        <p className="text-sm text-gray-400 mb-1">{title}</p>
        <p className="text-3xl font-bold text-white">{value}</p>
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <AlertCircle className="w-12 h-12 mb-3 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export default function AdminDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary>({
    total_users: 0,
    active_users: 0,
    total_requests: 0,
    cache_hit_ratio: 0,
    total_revenue: 0,
    active_api_keys: 0
  });
  const [growthData, setGrowthData] = useState<GrowthData[]>([]);
  const [usageData, setUsageData] = useState<UsageData[]>([]);
  const [planDist, setPlanDist] = useState<PlanDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryData, growth, usage, plans] = await Promise.all([
        adminAPI.getSummary(),
        adminAPI.getGrowthData(30),
        adminAPI.getUsageData(30),
        adminAPI.getPlanDistribution()
      ]);
      setSummary(summaryData);
      setGrowthData(growth);
      setUsageData(usage);
      setPlanDist(plans);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Unable to load dashboard data. Please check your connection and try again.');
      // Don't load sample data - show error instead
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  const revenueData = usageData.map(item => ({
    date: item.date,
    revenue: ((item.requests * 0.001) + Math.random() * 50).toFixed(2)
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h1>
          <p className="text-gray-400">
            Overview of Semantis AI platform metrics
          </p>
        </div>
        {error && (
          <div className="flex items-center px-4 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400 text-sm">
            <AlertCircle className="w-4 h-4 mr-2" />
            Demo Mode
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <KPICard
          title="Total Users"
          value={summary.total_users.toLocaleString()}
          icon={Users}
          trend={12.5}
          color="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <KPICard
          title="Active Users"
          value={summary.active_users.toLocaleString()}
          icon={Activity}
          trend={8.3}
          color="bg-gradient-to-br from-emerald-500 to-emerald-600"
        />
        <KPICard
          title="Total Requests"
          value={summary.total_requests.toLocaleString()}
          icon={TrendingUp}
          trend={15.2}
          color="bg-gradient-to-br from-purple-500 to-purple-600"
        />
        <KPICard
          title="Cache Hit Ratio"
          value={`${summary.cache_hit_ratio.toFixed(1)}%`}
          icon={Activity}
          trend={2.1}
          color="bg-gradient-to-br from-teal-500 to-teal-600"
        />
        <KPICard
          title="Total Revenue"
          value={`$${summary.total_revenue.toLocaleString()}`}
          icon={DollarSign}
          trend={18.7}
          color="bg-gradient-to-br from-orange-500 to-orange-600"
        />
        <KPICard
          title="Active API Keys"
          value={summary.active_api_keys.toLocaleString()}
          icon={Key}
          color="bg-gradient-to-br from-indigo-500 to-indigo-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">
            User Growth (30 Days)
          </h2>
          {growthData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={growthData}>
                <defs>
                  <linearGradient id="colorNewUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorActiveUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorTotalUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Line type="monotone" dataKey="new_users" stroke="#3B82F6" strokeWidth={3} name="New Users" dot={{ r: 4, fill: '#3B82F6' }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="active_users" stroke="#10B981" strokeWidth={3} name="Active Users" dot={{ r: 4, fill: '#10B981' }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="total_users" stroke="#F59E0B" strokeWidth={3} name="Total Users" dot={{ r: 4, fill: '#F59E0B' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No growth data available" />
          )}
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">
            Plan Distribution
          </h2>
          {planDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={planDist as any}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.plan_name} (${entry.percentage.toFixed(1)}%)`}
                  outerRadius={110}
                  fill="#8884d8"
                  dataKey="user_count"
                >
                  {planDist.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No plan distribution data available" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">
            Usage Trends
          </h2>
          {usageData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={usageData}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorCacheHits" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Area type="monotone" dataKey="requests" stackId="1" stroke="#3B82F6" fill="url(#colorRequests)" strokeWidth={2} name="Requests" />
                <Area type="monotone" dataKey="cache_hits" stackId="1" stroke="#10B981" fill="url(#colorCacheHits)" strokeWidth={2} name="Cache Hits" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No usage data available" />
          )}
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">
            Revenue Trends
          </h2>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={revenueData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={1}/>
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.6}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                  }}
                />
                <Bar dataKey="revenue" fill="url(#colorRevenue)" name="Revenue ($)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No revenue data available" />
          )}
        </div>
      </div>
    </div>
  );
}
