import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { statsAPI } from '../../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await statsAPI.get();
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <AdminLayout currentPage="dashboard">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
        </div>
      </AdminLayout>
    );
  }

  const statCards = [
    {
      title: 'Всего пользователей',
      value: stats?.total_users || 0,
      color: 'bg-blue-500',
      icon: '👥'
    },
    {
      title: 'Всего новостей',
      value: stats?.total_news || 0,
      color: 'bg-green-500',
      icon: '📰'
    },
    {
      title: 'Всего комментариев',
      value: stats?.total_comments || 0,
      color: 'bg-yellow-500',
      icon: '💬'
    },
    {
      title: 'Ожидают модерации',
      value: stats?.pending_comments || 0,
      color: 'bg-red-500',
      icon: '⏳'
    },
  ];

  return (
    <AdminLayout currentPage="dashboard">
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>
          <p className="text-gray-600">Обзор системы управления школьным сайтом</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((card, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-3xl font-bold text-gray-900">{card.value}</p>
                </div>
                <div className={`p-3 rounded-full ${card.color}`}>
                  <span className="text-2xl">{card.icon}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Быстрые действия</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <a
                href="/admin/news"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-2xl mr-3">📰</span>
                  <div>
                    <h3 className="font-medium text-gray-900">Создать новость</h3>
                    <p className="text-sm text-gray-600">Добавить новую новость</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/admin/gallery"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🖼️</span>
                  <div>
                    <h3 className="font-medium text-gray-900">Загрузить в галерею</h3>
                    <p className="text-sm text-gray-600">Добавить новые фотографии</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/admin/comments"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-2xl mr-3">💬</span>
                  <div>
                    <h3 className="font-medium text-gray-900">Модерировать комментарии</h3>
                    <p className="text-sm text-gray-600">Проверить новые комментарии</p>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Информация о системе</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Статистика сайта</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>Всего посещений: {stats?.total_visits || 0}</li>
                  <li>Посещений сегодня: {stats?.daily_visits || 0}</li>
                  <li>Последнее обновление: {new Date().toLocaleString('ru-RU')}</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Состояние системы</h3>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-600">API работает</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-600">База данных подключена</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-600">Сайт доступен</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default Dashboard;