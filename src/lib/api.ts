const API_URL = "http://localhost:8000/api";

interface RequestOptions extends RequestInit {
  data?: unknown;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { data, ...customConfig } = options;
  
  const headers = {
    "Content-Type": "application/json",
    ...customConfig.headers,
  };

  const config: RequestInit = {
    method: options.method || "GET",
    headers,
    credentials: "include", // Important for Session Auth
    ...customConfig,
  };

  if (data) {
    config.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_URL}${endpoint}`, config);
  
  // Handle 401 Unauthorized globally if needed (e.g., redirect to login)
  if (response.status === 401) {
    // Optionally trigger logout or refresh
    // For now just throw error
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || "Something went wrong";
    throw new Error(message);
  }

  // Handle empty responses (like 204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "GET" }),
    
  post: <T>(endpoint: string, data: unknown, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "POST", data }),
    
  put: <T>(endpoint: string, data: unknown, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "PUT", data }),

  patch: <T>(endpoint: string, data: unknown, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "PATCH", data }),
    
  delete: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "DELETE" }),
};
