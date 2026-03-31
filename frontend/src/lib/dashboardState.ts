/**
 * Global state management for dashboard initialization
 * Ensures loading screens only show once after login
 */

let dashboardInitialized = false;

export const setDashboardInitialized = () => {
  dashboardInitialized = true;
};

export const isDashboardInitialized = () => {
  return dashboardInitialized;
};

export const resetDashboardState = () => {
  dashboardInitialized = false;
};

