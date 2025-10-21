"use client";

import React, { useEffect, useState } from 'react';
import {
  Search,
  Bell,
  TrendingUp,
  TrendingDown,
  Package,
  Clock,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Activity
} from 'lucide-react';
import Sidebar from './Sidebar';

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
  delay: number;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, trend, icon, color, delay }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`stat-card bg-white rounded-xl p-6 shadow-sm hover:shadow-xl border border-gray-100 transition-all duration-500 transform ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <h3 className="text-3xl font-bold text-gray-900 mt-2">{value}</h3>
          <div className="flex items-center gap-1 mt-3">
            {trend === 'up' ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            <span className={`text-sm font-medium ${trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
              {change}
            </span>
            <span className="text-sm text-gray-500">vs last month</span>
          </div>
        </div>
        <div className={`${color} p-3 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [searchFocused, setSearchFocused] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const stats = [
    {
      title: 'Active Prescriptions',
      value: '128',
      change: '+12.5%',
      trend: 'up' as const,
      icon: <Activity className="w-6 h-6 text-blue-600" />,
      color: 'bg-blue-50',
    },
    {
      title: 'Pending Orders',
      value: '21',
      change: '-5.2%',
      trend: 'down' as const,
      icon: <Clock className="w-6 h-6 text-amber-600" />,
      color: 'bg-amber-50',
    },
    {
      title: 'Medications in Stock',
      value: '3,420',
      change: '+8.1%',
      trend: 'up' as const,
      icon: <Package className="w-6 h-6 text-green-600" />,
      color: 'bg-green-50',
    },
    {
      title: 'Revenue (Today)',
      value: '$4,582',
      change: '+15.3%',
      trend: 'up' as const,
      icon: <DollarSign className="w-6 h-6 text-purple-600" />,
      color: 'bg-purple-50',
    },
  ];

  const recentActivity = [
    {
      id: 1,
      type: 'success',
      icon: <CheckCircle className="w-5 h-5 text-green-500" />,
      title: 'Order #PH-1023 fulfilled',
      time: '2h ago',
    },
    {
      id: 2,
      type: 'info',
      icon: <Activity className="w-5 h-5 text-blue-500" />,
      title: 'New prescription added for John D.',
      time: '3h ago',
    },
    {
      id: 3,
      type: 'warning',
      icon: <AlertTriangle className="w-5 h-5 text-amber-500" />,
      title: 'Low stock alert: Omeprazole',
      time: '1d ago',
    },
    {
      id: 4,
      type: 'success',
      icon: <CheckCircle className="w-5 h-5 text-green-500" />,
      title: 'Inventory restocked: 15 items',
      time: '2d ago',
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-gray-50 to-blue-50">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-20 transition-all duration-300">
          <div className="p-4 md:p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-1 max-w-2xl">
                <div
                  className={`flex items-center bg-white rounded-xl px-4 py-3 flex-1 border-2 transition-all duration-300 ${
                    searchFocused ? 'border-blue-500 shadow-lg' : 'border-gray-200 shadow-sm'
                  }`}
                >
                  <Search className={`w-5 h-5 transition-colors duration-300 ${searchFocused ? 'text-blue-600' : 'text-gray-400'}`} />
                  <input
                    type="text"
                    placeholder="Search medications, orders, patients..."
                    className="ml-3 bg-transparent border-none focus:outline-none placeholder:text-gray-400 text-gray-900 flex-1"
                    onFocus={() => setSearchFocused(true)}
                    onBlur={() => setSearchFocused(false)}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button className="relative p-3 rounded-xl hover:bg-gray-100 transition-all duration-200 group">
                  <Bell className="w-5 h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
                  <span className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex items-center justify-center rounded-full h-5 w-5 bg-red-500 text-white text-xs font-bold">
                      3
                    </span>
                  </span>
                </button>
                <div className="relative group">
                  <img
                    src="https://i.pravatar.cc/300"
                    alt="User avatar"
                    className="w-10 h-10 rounded-xl border-2 border-white shadow-md group-hover:shadow-lg transition-all duration-200 cursor-pointer"
                  />
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8 animate-fade-in">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Dashboard</h2>
              <p className="text-gray-600 mt-2">Quick overview of pharmacy operations</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {stats.map((stat, index) => (
                <StatCard key={index} {...stat} delay={index * 100} />
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100 animate-slide-up">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Recent Activity</h3>
                  <button className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors">
                    View All
                  </button>
                </div>
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div
                      key={activity.id}
                      className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 transition-all duration-200 cursor-pointer group animate-slide-in"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex-shrink-0 group-hover:scale-110 transition-transform duration-200">
                        {activity.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                          {activity.title}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 flex-shrink-0">{activity.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl p-6 text-white shadow-lg animate-fade-in">
                <h3 className="text-xl font-bold mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg p-3 text-left transition-all duration-200 hover:translate-x-1">
                    <p className="font-medium">Add New Prescription</p>
                  </button>
                  <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg p-3 text-left transition-all duration-200 hover:translate-x-1">
                    <p className="font-medium">Process Order</p>
                  </button>
                  <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg p-3 text-left transition-all duration-200 hover:translate-x-1">
                    <p className="font-medium">Update Inventory</p>
                  </button>
                  <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg p-3 text-left transition-all duration-200 hover:translate-x-1">
                    <p className="font-medium">Generate Report</p>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;