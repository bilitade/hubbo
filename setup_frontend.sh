#\!/bin/bash

cd /home/bilisuma/Desktop/RBAC/frontend

# Create types
cat > src/types/index.ts << 'EOF'
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  is_active: boolean;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
  roles: Role[];
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: Permission[];
}

export interface Permission {
  id: number;
  name: string;
  description?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}
EOF

# Create API service
cat > src/services/api.ts << 'EOF'
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const tokens = localStorage.getItem('tokens');
        if (tokens) {
          const { access_token } = JSON.parse(tokens);
          config.headers.Authorization = `Bearer ${access_token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && originalRequest) {
          try {
            const tokens = localStorage.getItem('tokens');
            if (tokens) {
              const { refresh_token } = JSON.parse(tokens);
              const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                refresh_token,
              });
              
              const newTokens = response.data;
              localStorage.setItem('tokens', JSON.stringify(newTokens));
              
              originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            localStorage.removeItem('tokens');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await this.api.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  async logout(refreshToken: string) {
    return this.api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
  }

  async getCurrentUser() {
    const response = await this.api.get('/api/v1/users/me');
    return response.data;
  }

  // User endpoints
  async getUsers() {
    const response = await this.api.get('/api/v1/users');
    return response.data;
  }

  async getUser(id: number) {
    const response = await this.api.get(`/api/v1/users/${id}`);
    return response.data;
  }

  async createUser(userData: any) {
    const response = await this.api.post('/api/v1/users', userData);
    return response.data;
  }

  async updateUser(id: number, userData: any) {
    const response = await this.api.patch(`/api/v1/users/${id}`, userData);
    return response.data;
  }

  async deleteUser(id: number) {
    return this.api.delete(`/api/v1/users/${id}`);
  }

  // Role endpoints
  async getRoles() {
    const response = await this.api.get('/api/v1/roles');
    return response.data;
  }

  // Permission endpoints
  async getPermissions() {
    const response = await this.api.get('/api/v1/permissions');
    return response.data;
  }
}

export const apiService = new ApiService();
EOF

echo "✅ Setup complete\!"
