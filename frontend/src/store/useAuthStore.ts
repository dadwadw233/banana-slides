import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/api/endpoints';
import * as api from '@/api/endpoints';
import { apiClient } from '@/api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.login(email, password);
          const { user, access_token } = response.data!;
          
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error?.code || '登录失败';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.register(email, password);
          const { user, access_token } = response.data!;
          
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error?.code || '注册失败';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      logout: () => {
        delete apiClient.defaults.headers.common['Authorization'];
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshUser: async () => {
        const { token } = get();
        if (!token) return;

        try {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          const response = await api.getCurrentUser();
          set({ user: response.data!.user });
        } catch (error) {
          get().logout();
        }
      },

      setError: (error: string | null) => set({ error }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${state.token}`;
        }
      },
    }
  )
);
