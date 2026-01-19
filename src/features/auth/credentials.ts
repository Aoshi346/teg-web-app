// Test users for local/demo login with roles
export const TEST_USERS = [
  { email: 'admin@example.com', password: '1234', role: 'Admin' },
  { email: 'estudiante@example.com', password: 'est123', role: 'Estudiante' },
  { email: 'profesor@example.com', password: 'prof123', role: 'Profesor' },
];

// Backwards-compatible single exported constants (deprecated but kept for convenience)
export const DEFAULT_TEST_USER = TEST_USERS[0].email;
export const DEFAULT_TEST_PASSWORD = TEST_USERS[0].password;
