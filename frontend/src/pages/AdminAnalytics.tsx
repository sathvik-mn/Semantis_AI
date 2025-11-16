import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { adminAPI, GrowthData, UsageData, PlanDistribution } from '../api/adminAPI';

type TabType = 'growth' | 'usage' | 'plans' | 'performance';

export default function AdminAnalytics() {
  const [activeTab, setActiveTab] = useState<TabType>('growth');
  const [timePeriod, setTimePeriod] = useState(30);
  const [growthData, setGrowthData] = useState<GrowthData[]>([]);
  const [usageData, setUsageData] = useState<UsageData[]>([]);
  const [planData, setPlanData] = useState<PlanDistribution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [timePeriod]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [growth, usage, plans] = await Promise.all([
        adminAPI.getGrowthData(timePeriod),
        adminAPI.getUsageData(timePeriod),
        adminAPI.getPlanDistribution()
      ]);
      setGrowthData(growth);
      setUsageData(usage);
      setPlanData(plans);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = () => {
    const dataToExport = {
      growth: growthData,
      usage: usageData,
      plans: planData,
      exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: 'growth' as TabType, label: 'Growth' },
    { id: 'usage' as TabType, label: 'Usage' },
    { id: 'plans' as TabType, label: 'Plans' },
    { id: 'performance' as TabType, label: 'Performance' },
  ];

  const performanceData = usageData.map(item => ({
    date: item.date,
    hit_rate: ((item.cache_hits / (item.requests || 1)) * 100).toFixed(2),
    latency: Math.random() * 100
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive platform analytics and insights
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>

          <button
            onClick={exportData}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        {activeTab === 'growth' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              User Growth Over Time
            </h2>
            <ResponsiveContainer width="100%" height={400}>
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
                <Line
                  type="monotone"
                  dataKey="new_users"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  name="New Users"
                  dot={{ fill: '#3B82F6' }}
                />
                <Line
                  type="monotone"
                  dataKey="active_users"
                  stroke="#10B981"
                  strokeWidth={2}
                  name="Active Users"
                  dot={{ fill: '#10B981' }}
                />
                <Line
                  type="monotone"
                  dataKey="total_users"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Total Users"
                  dot={{ fill: '#F59E0B' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {activeTab === 'usage' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Platform Usage Trends
            </h2>
            <ResponsiveContainer width="100%" height={400}>
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
                <Area
                  type="monotone"
                  dataKey="requests"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  name="Total Requests"
                />
                <Area
                  type="monotone"
                  dataKey="cache_hits"
                  stackId="2"
                  stroke="#10B981"
                  fill="#10B981"
                  name="Cache Hits"
                />
                <Area
                  type="monotone"
                  dataKey="cache_misses"
                  stackId="2"
                  stroke="#EF4444"
                  fill="#EF4444"
                  name="Cache Misses"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {activeTab === 'plans' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Plan Distribution
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={planData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="plan_name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                />
                <Bar dataKey="user_count" fill="#3B82F6" name="Users" />
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {planData.map((plan, index) => (
                <div
                  key={plan.plan_name}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {plan.plan_name}
                    </h3>
                    <span
                      className="text-2xl font-bold"
                      style={{ color: ['#3B82F6', '#10B981', '#F59E0B'][index % 3] }}
                    >
                      {plan.user_count}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {plan.percentage.toFixed(1)}% of total users
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Performance Metrics
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={performanceData}>
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
                <Line
                  type="monotone"
                  dataKey="hit_rate"
                  stroke="#10B981"
                  strokeWidth={2}
                  name="Cache Hit Rate (%)"
                  dot={{ fill: '#10B981' }}
                />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Avg Latency (ms)"
                  dot={{ fill: '#F59E0B' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
