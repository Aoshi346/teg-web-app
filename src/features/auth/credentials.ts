export const TEST_USERS = [
  { email: 'admin@tesisfar.com', password: 'admin', role: 'Administrador' },
  { email: 'estudiante@example.com', password: 'est123', role: 'Estudiante' },
  { email: 'tutor@example.com', password: 'prof123', role: 'Tutor' },
  { email: 'jurado@example.com', password: 'jur123', role: 'Jurado' },
];

// Backwards-compatible single exported constants (deprecated but kept for convenience)
export const DEFAULT_TEST_USER = TEST_USERS[0].email;
export const DEFAULT_TEST_PASSWORD = TEST_USERS[0].password;
