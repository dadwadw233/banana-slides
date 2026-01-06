import React, { useEffect, useState } from 'react';
import { getQuotaBalance } from '@/api/endpoints';
import { useAuthStore } from '@/store/useAuthStore';
import { Sparkles, RefreshCw } from 'lucide-react';

interface QuotaDisplayProps {
  className?: string;
  refreshInterval?: number; // ms, default 30000
}

export const QuotaDisplay: React.FC<QuotaDisplayProps> = ({ 
  className = '', 
  refreshInterval = 30000 
}) => {
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuthStore();

  const fetchQuota = async () => {
    if (!isAuthenticated) {
      setBalance(null);
      return;
    }
    
    try {
      setLoading(true);
      const res = await getQuotaBalance();
      if (res.data) {
        setBalance(res.data.balance);
      }
    } catch (error) {
      console.error('Failed to fetch quota', error);
      setBalance(null); 
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuota();
    const interval = setInterval(fetchQuota, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, isAuthenticated]);

  if (balance === null) return null;

  return (
    <div className={`flex items-center gap-1.5 px-3 py-1.5 bg-yellow-50 text-yellow-700 rounded-full text-sm font-medium border border-yellow-200 ${className}`}>
      <Sparkles size={14} className="text-yellow-500" />
      <span>{balance} 次</span>
      <button 
        onClick={fetchQuota} 
        className={`ml-1 hover:text-yellow-800 transition-colors ${loading ? 'animate-spin' : ''}`}
        title="刷新配额"
      >
        <RefreshCw size={12} />
      </button>
    </div>
  );
};
