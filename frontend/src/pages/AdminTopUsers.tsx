import { useEffect, useState } from 'react';
import { Trophy, TrendingUp, DollarSign } from 'lucide-react';
import { adminAPI, TopUser } from '../api/adminAPI';

export default function AdminTopUsers() {
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [sortBy, setSortBy] = useState<'requests' | 'hits' | 'savings'>('requests');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTopUsers();
  }, [sortBy]);

  const loadTopUsers = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getTopUsers(100, sortBy);
      setTopUsers(data);
    } catch (error) {
      console.error('Error loading top users:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrophyColor = (rank: number) => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-gray-400';
    if (rank === 3) return 'text-orange-600';
    return 'text-gray-300 dark:text-gray-600';
  };

  const getRankBg = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-2 border-yellow-300';
    if (rank === 2) return 'bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800/20 dark:to-gray-700/20 border-2 border-gray-300';
    if (rank === 3) return 'bg-gradient-to-r from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-2 border-orange-300';
    return 'bg-white dark:bg-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading top users...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Top Users</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Leaderboard of highest performing users
          </p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setSortBy('requests')}
            className={`px-4 py-2 rounded-lg font-medium ${
              sortBy === 'requests'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            By Requests
          </button>
          <button
            onClick={() => setSortBy('hits')}
            className={`px-4 py-2 rounded-lg font-medium ${
              sortBy === 'hits'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            By Cache Hits
          </button>
          <button
            onClick={() => setSortBy('savings')}
            className={`px-4 py-2 rounded-lg font-medium ${
              sortBy === 'savings'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            By Savings
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {topUsers.slice(0, 3).map((user, index) => (
          <div
            key={user.tenant_id}
            className={`${getRankBg(index + 1)} rounded-lg shadow-lg p-6 transform hover:scale-105 transition-transform`}
          >
            <div className="flex items-center justify-between mb-4">
              <Trophy className={`w-12 h-12 ${getTrophyColor(index + 1)}`} />
              <span className="text-4xl font-bold text-gray-300 dark:text-gray-600">
                #{index + 1}
              </span>
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
              {user.company_name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{user.email}</p>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Requests</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {user.total_requests.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Cache Hits</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {user.cache_hits.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Cost Saved</span>
                <span className="font-semibold text-green-600 dark:text-green-400">
                  ${user.cost_saved.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  <div className="flex items-center justify-end">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    Requests
                  </div>
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cache Hits
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  <div className="flex items-center justify-end">
                    <DollarSign className="w-4 h-4 mr-1" />
                    Cost Saved
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {topUsers.map((user, index) => (
                <tr
                  key={user.tenant_id}
                  className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${
                    index < 3 ? 'font-semibold' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {index < 3 && (
                        <Trophy className={`w-5 h-5 mr-2 ${getTrophyColor(index + 1)}`} />
                      )}
                      <span className="text-sm text-gray-900 dark:text-white">
                        #{user.rank}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {user.company_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-white">
                    {user.total_requests.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-white">
                    {user.cache_hits.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 dark:text-green-400 font-semibold">
                    ${user.cost_saved.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
