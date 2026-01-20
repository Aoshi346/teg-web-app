const API_URL = "http://localhost:8000/api";

// Helper: read csrftoken from cookie
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [key, ...rest] = cookie.trim().split("=");
    if (key === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

interface RequestOptions extends RequestInit {
  data?: unknown;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { data, ...customConfig } = options;
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customConfig.headers as Record<string, string>) || {}),
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

  // Attach CSRF for unsafe methods
  const unsafeMethods = ["POST", "PUT", "PATCH", "DELETE"];
  const method = (config.method || "GET").toUpperCase();
  if (unsafeMethods.includes(method)) {
    // Ensure we have a CSRF token cookie; if not, fetch it
    let csrfToken = getCookie("csrftoken");
    if (!csrfToken) {
      try {
        // Fetch CSRF token to set cookie
        await fetch(`${API_URL}/csrf/`, { credentials: "include" });
        csrfToken = getCookie("csrftoken");
      } catch (e) {
        // proceed; server may still accept if CSRF is exempt in dev
      }
    }
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }
  }

  const response = await fetch(`${API_URL}${endpoint}`, config);
  
  // Handle 401 Unauthorized globally if needed (e.g., redirect to login)
  if (response.status === 401) {
    // Optionally trigger logout or refresh
    // For now just throw error
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let message = errorData.detail || errorData.message;

    if (!message && errorData && typeof errorData === "object") {
      const firstKey = Object.keys(errorData)[0];
      const value = (errorData as Record<string, unknown>)[firstKey];
      if (Array.isArray(value) && value.length > 0 && typeof value[0] === "string") {
        message = value[0];
      }
    }

    if (!message) message = "Something went wrong";
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
