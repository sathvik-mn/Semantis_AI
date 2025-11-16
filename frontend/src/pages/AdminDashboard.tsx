import { useEffect, useState } from 'react';
import { Users, Activity, DollarSign, Key, TrendingUp, TrendingDown } from 'lucide-react';
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 transition-colors">
      <div className="flex items-center justify-between">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
            <span className="text-sm font-semibold">{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
      </div>
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

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
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
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  const revenueData = usageData.map(item => ({
    date: item.date,
    revenue: (item.requests * 0.001).toFixed(2)
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of Semantis AI platform metrics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <KPICard
          title="Total Users"
          value={summary.total_users.toLocaleString()}
          icon={Users}
          trend={12.5}
          color="bg-blue-500"
        />
        <KPICard
          title="Active Users"
          value={summary.active_users.toLocaleString()}
          icon={Activity}
          trend={8.3}
          color="bg-green-500"
        />
        <KPICard
          title="Total Requests"
          value={summary.total_requests.toLocaleString()}
          icon={TrendingUp}
          trend={15.2}
          color="bg-purple-500"
        />
        <KPICard
          title="Cache Hit Ratio"
          value={`${summary.cache_hit_ratio.toFixed(1)}%`}
          icon={Activity}
          trend={2.1}
          color="bg-emerald-500"
        />
        <KPICard
          title="Total Revenue"
          value={`$${summary.total_revenue.toLocaleString()}`}
          icon={DollarSign}
          trend={18.7}
          color="bg-orange-500"
        />
        <KPICard
          title="Active API Keys"
          value={summary.active_api_keys.toLocaleString()}
          icon={Key}
          color="bg-indigo-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            User Growth (30 Days)
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="new_users" stroke="#3B82F6" name="New Users" strokeWidth={2} />
              <Line type="monotone" dataKey="active_users" stroke="#10B981" name="Active Users" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Plan Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={planDist as any}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => entry.plan_name}
                outerRadius={100}
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
                  border: 'none',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Usage Trends
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={usageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="requests" stackId="1" stroke="#3B82F6" fill="#3B82F6" name="Requests" />
              <Area type="monotone" dataKey="cache_hits" stackId="1" stroke="#10B981" fill="#10B981" name="Cache Hits" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Revenue Trends
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#F9FAFB'
                }}
              />
              <Bar dataKey="revenue" fill="#F59E0B" name="Revenue ($)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
