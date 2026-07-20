import axios from "axios";

const API_BASE = "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach JWT token to every outgoing request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// On 401 responses, clear auth state and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user_id");
      localStorage.removeItem("user_role");
      localStorage.removeItem("user_name");
      localStorage.removeItem("profile_image");
      // Only redirect if we're not already on the login/register pages
      const path = window.location.pathname;
      if (!path.startsWith("/login") && !path.startsWith("/register") && path !== "/") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
export { API_BASE };
