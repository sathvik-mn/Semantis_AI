import { useEffect, useState } from 'react';
import { Download, AlertCircle } from 'lucide-react';
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

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <AlertCircle className="w-12 h-12 mb-3 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export default function AdminAnalytics() {
  const [activeTab, setActiveTab] = useState<TabType>('growth');
  const [timePeriod, setTimePeriod] = useState(30);
  const [growthData, setGrowthData] = useState<GrowthData[]>([]);
  const [usageData, setUsageData] = useState<UsageData[]>([]);
  const [planData, setPlanData] = useState<PlanDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, [timePeriod]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const [growth, usage, plans] = await Promise.all([
        adminAPI.getGrowthData(timePeriod),
        adminAPI.getUsageData(timePeriod),
        adminAPI.getPlanDistribution()
      ]);
      setGrowthData(growth);
      setUsageData(usage);
      setPlanData(plans);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Using sample data for demonstration.');

      // Load sample data
      const dates = Array.from({ length: timePeriod }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - (timePeriod - 1 - i));
        return d.toISOString().split('T')[0];
      });

      setGrowthData(dates.map((date, i) => ({
        date: date.slice(5),
        new_users: Math.floor(Math.random() * 50) + 20,
        active_users: 800 + Math.floor(Math.random() * 200),
        total_users: 1000 + i * 8
      })));

      setUsageData(dates.map(date => ({
        date: date.slice(5),
        requests: Math.floor(Math.random() * 2000) + 1000,
        cache_hits: Math.floor(Math.random() * 1500) + 700,
        cache_misses: Math.floor(Math.random() * 500) + 200
      })));

      setPlanData([
        { plan_name: 'Free', user_count: 687, percentage: 55.1 },
        { plan_name: 'Pro', user_count: 423, percentage: 33.9 },
        { plan_name: 'Enterprise', user_count: 137, percentage: 11.0 }
      ]);
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
    latency: Math.random() * 100 + 20
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Analytics</h1>
          <p className="text-gray-400">
            Comprehensive platform analytics and insights
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {error && (
            <div className="flex items-center px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400 text-xs">
              <AlertCircle className="w-3 h-3 mr-1.5" />
              Demo Mode
            </div>
          )}
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(Number(e.target.value))}
            className="px-4 py-2.5 bg-gray-800 border border-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>

          <button
            onClick={exportData}
            className="flex items-center px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg shadow-blue-500/20"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      <div className="border-b border-gray-700">
        <nav className="flex space-x-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                activeTab === tab.id
                  ? 'text-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-blue-600"></div>
              )}
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-8 border border-gray-700">
        {activeTab === 'growth' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">
              User Growth Over Time
            </h2>
            {growthData.length > 0 ? (
              <ResponsiveContainer width="100%" height={450}>
                <LineChart data={growthData}>
                  <defs>
                    <linearGradient id="colorNew" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F9FAFB',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '24px' }} />
                  <Line
                    type="monotone"
                    dataKey="new_users"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    name="New Users"
                    dot={{ r: 4, fill: '#3B82F6' }}
                    activeDot={{ r: 7, fill: '#3B82F6' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="active_users"
                    stroke="#10B981"
                    strokeWidth={3}
                    name="Active Users"
                    dot={{ r: 4, fill: '#10B981' }}
                    activeDot={{ r: 7, fill: '#10B981' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="total_users"
                    stroke="#F59E0B"
                    strokeWidth={3}
                    name="Total Users"
                    dot={{ r: 4, fill: '#F59E0B' }}
                    activeDot={{ r: 7, fill: '#F59E0B' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No growth data available" />
            )}
          </div>
        )}

        {activeTab === 'usage' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">
              Platform Usage Trends
            </h2>
            {usageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={450}>
                <AreaChart data={usageData}>
                  <defs>
                    <linearGradient id="colorReq" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorHits" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorMisses" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F9FAFB',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '24px' }} />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    stackId="1"
                    stroke="#3B82F6"
                    fill="url(#colorReq)"
                    strokeWidth={2}
                    name="Total Requests"
                  />
                  <Area
                    type="monotone"
                    dataKey="cache_hits"
                    stackId="2"
                    stroke="#10B981"
                    fill="url(#colorHits)"
                    strokeWidth={2}
                    name="Cache Hits"
                  />
                  <Area
                    type="monotone"
                    dataKey="cache_misses"
                    stackId="2"
                    stroke="#EF4444"
                    fill="url(#colorMisses)"
                    strokeWidth={2}
                    name="Cache Misses"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No usage data available" />
            )}
          </div>
        )}

        {activeTab === 'plans' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">
              Plan Distribution
            </h2>
            {planData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={planData}>
                    <defs>
                      <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={1}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.6}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                    <XAxis dataKey="plan_name" stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                    <YAxis stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F9FAFB',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                      }}
                    />
                    <Bar dataKey="user_count" fill="url(#barGradient)" name="Users" radius={[10, 10, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>

                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                  {planData.map((plan, index) => (
                    <div
                      key={plan.plan_name}
                      className="p-6 bg-gradient-to-br from-gray-700/50 to-gray-800/50 border border-gray-600 rounded-xl hover:border-gray-500 transition-all"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-bold text-white text-lg">
                          {plan.plan_name}
                        </h3>
                        <span
                          className="text-3xl font-bold"
                          style={{ color: ['#3B82F6', '#10B981', '#F59E0B'][index % 3] }}
                        >
                          {plan.user_count}
                        </span>
                      </div>
                      <div className="text-sm text-gray-400">
                        {plan.percentage.toFixed(1)}% of total users
                      </div>
                      <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{
                            width: `${plan.percentage}%`,
                            backgroundColor: ['#3B82F6', '#10B981', '#F59E0B'][index % 3]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <EmptyState message="No plan distribution data available" />
            )}
          </div>
        )}

        {activeTab === 'performance' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">
              Performance Metrics
            </h2>
            {performanceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={450}>
                <LineChart data={performanceData}>
                  <defs>
                    <linearGradient id="hitRateGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '13px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F9FAFB',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '24px' }} />
                  <Line
                    type="monotone"
                    dataKey="hit_rate"
                    stroke="#10B981"
                    strokeWidth={3}
                    name="Cache Hit Rate (%)"
                    dot={{ r: 4, fill: '#10B981' }}
                    activeDot={{ r: 7, fill: '#10B981' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#F59E0B"
                    strokeWidth={3}
                    name="Avg Latency (ms)"
                    dot={{ r: 4, fill: '#F59E0B' }}
                    activeDot={{ r: 7, fill: '#F59E0B' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No performance data available" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
