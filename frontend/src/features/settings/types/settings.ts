export type SettingsTabId = "profile" | "security" | "notifications" | "admin";
export type AdminSubTabId = "pending" | "directory" | "semesters";

export interface AccountMetadata {
  role: string;
  dateJoined: string;
  lastLogin: string | null;
  semesterPeriod: string | null;
}
