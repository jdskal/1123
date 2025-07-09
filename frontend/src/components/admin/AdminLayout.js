import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  HomeIcon, 
  NewspaperIcon, 
  InformationCircleIcon, 
  PhotoIcon, 
  PhoneIcon, 
  CalendarIcon, 
  ChatBubbleLeftEllipsisIcon,
  UsersIcon,
  ChartBarIcon,
  Bars3Icon,
  XMarkIcon,
  LogoutIcon
} from '@heroicons/react/24/outline';

const AdminLayout = ({ children, currentPage }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();

  const navigation = [
    { name: 'Дашборд', href: '/admin', icon: HomeIcon, current: currentPage === 'dashboard' },
    { name: 'Новости', href: '/admin/news', icon: NewspaperIcon, current: currentPage === 'news' },
    { name: 'О школе', href: '/admin/school-info', icon: InformationCircleIcon, current: currentPage === 'school-info' },
    { name: 'Галерея', href: '/admin/gallery', icon: PhotoIcon, current: currentPage === 'gallery' },
    { name: 'Контакты', href: '/admin/contacts', icon: PhoneIcon, current: currentPage === 'contacts' },
    { name: 'Расписание', href: '/admin/schedule', icon: CalendarIcon, current: currentPage === 'schedule' },
    { name: 'Комментарии', href: '/admin/comments', icon: ChatBubbleLeftEllipsisIcon, current: currentPage === 'comments' },
    { name: 'Пользователи', href: '/admin/users', icon: UsersIcon, current: currentPage === 'users', adminOnly: true },
    { name: 'Статистика', href: '/admin/stats', icon: ChartBarIcon, current: currentPage === 'stats' },
  ];

  const filteredNavigation = navigation.filter(item => 
    !item.adminOnly || (item.adminOnly && user?.role === 'admin')
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-40 md:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" />
            </button>
          </div>
          <SidebarContent navigation={filteredNavigation} user={user} logout={logout} />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
          <SidebarContent navigation={filteredNavigation} user={user} logout={logout} />
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        <div className="sticky top-0 z-10 md:hidden pl-1 pt-1 sm:pl-3 sm:pt-3 bg-gray-100">
          <button
            className="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>
        
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

const SidebarContent = ({ navigation, user, logout }) => {
  return (
    <>
      <div className="flex items-center h-16 px-4 bg-indigo-600">
        <h1 className="text-xl font-bold text-white">Админ-панель</h1>
      </div>
      
      <div className="flex-1 flex flex-col overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => (
            <a
              key={item.name}
              href={item.href}
              className={`
                group flex items-center px-2 py-2 text-sm font-medium rounded-md
                ${item.current 
                  ? 'bg-indigo-100 text-indigo-900' 
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }
              `}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </a>
          ))}
        </nav>
      </div>
      
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user?.full_name?.charAt(0) || 'A'}
              </span>
            </div>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">{user?.full_name}</p>
            <p className="text-xs text-gray-500">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <LogoutIcon className="h-4 w-4 mr-2" />
          Выйти
        </button>
      </div>
    </>
  );
};

export default AdminLayout;