import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { LogOut } from 'lucide-react';

export const UserMenu: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!isAuthenticated) {
    return (
      <button
        onClick={() => navigate('/login')}
        className={`text-sm font-medium text-gray-600 hover:text-yellow-600 transition-colors ${className}`}
      >
        登录
      </button>
    );
  }

  const displayName = user?.username || user?.email?.split('@')[0] || 'User';
  const initial = displayName[0].toUpperCase();

  return (
    <div className={`relative ${className}`} ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 focus:outline-none"
      >
        <div className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-semibold border border-yellow-200">
          {initial}
        </div>
        <span className="text-sm font-medium text-gray-700 hidden md:block max-w-[100px] truncate">
          {displayName}
        </span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 border border-gray-200 z-50">
          <div className="px-4 py-2 border-b border-gray-100">
            <p className="text-xs text-gray-500">已登录为</p>
            <p className="text-sm font-medium text-gray-900 truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => {
              logout();
              setIsOpen(false);
              navigate('/login');
            }}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <LogOut size={14} />
            退出登录
          </button>
        </div>
      )}
    </div>
  );
};
