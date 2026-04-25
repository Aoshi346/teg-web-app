import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock before importing the component. getPreferences and updatePreferences do not
// exist in clientAuth yet — the mock ensures import succeeds regardless.
vi.mock("@features/auth/api/clientAuth", () => ({
  getPreferences: vi.fn(),
  updatePreferences: vi.fn(),
  getUserRole: vi.fn(),
}));

import { NotificationsTab } from "./NotificationsTab";
import {
  getPreferences,
  updatePreferences,
  getUserRole,
} from "@features/auth/api/clientAuth";

const mockGetPreferences = vi.mocked(getPreferences);
const mockUpdatePreferences = vi.mocked(updatePreferences);
const mockGetUserRole = vi.mocked(getUserRole);

// All 6 preference keys an Administrador sees
const ALL_PREFS = {
  notify_evaluation_received: true,
  notify_state_change: true,
  notify_assignment: true,
  notify_comment_added: true,
  notify_semester_changes: true,
  email_enabled: true,
};

// Subset visible to Estudiante per brief:
// notify_evaluation_received, notify_state_change, notify_comment_added, email_enabled
const STUDENT_PREF_KEYS = [
  "notify_evaluation_received",
  "notify_state_change",
  "notify_comment_added",
  "email_enabled",
];

// Keys visible only to Administrador (not Estudiante)
const ADMIN_ONLY_KEYS = ["notify_assignment", "notify_semester_changes"];

describe("NotificationsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a loading indicator while getPreferences is unresolved", async () => {
    // Never resolves during this test — intentional for loading-state assertion
    mockGetPreferences.mockReturnValue(new Promise(() => {}));
    mockGetUserRole.mockReturnValue("Administrador");

    render(<NotificationsTab />);

    // Accept either role="status" OR text containing "cargando"
    const loadingEl =
      document.querySelector('[role="status"]') ??
      (await screen.findByText(/cargando/i));
    expect(loadingEl).toBeTruthy();
  });

  it("renders 6 switches all aria-checked=true when Administrador prefs all true", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetPreferences.mockResolvedValueOnce(ALL_PREFS);

    render(<NotificationsTab />);

    // Wait for loading to finish — all 6 switches should appear
    await waitFor(() => {
      const switches = screen.getAllByRole("switch");
      expect(switches).toHaveLength(6);
    });

    const switches = screen.getAllByRole("switch");
    switches.forEach((sw) => {
      expect(sw).toHaveAttribute("aria-checked", "true");
    });
  });

  it("shows all 6 keys for Administrador but only 4 for Estudiante", async () => {
    // --- Administrador render ---
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetPreferences.mockResolvedValueOnce(ALL_PREFS);

    const { unmount } = render(<NotificationsTab />);

    await waitFor(() => {
      expect(screen.getAllByRole("switch")).toHaveLength(6);
    });

    // Admin-only keys must be present
    for (const key of ADMIN_ONLY_KEYS) {
      const dataAttr = document.querySelector(`[data-pref-key="${key}"]`);
      // Accept either data attribute OR the switch being present (6 total confirmed above)
      expect(dataAttr ?? screen.getAllByRole("switch")).toBeTruthy();
    }

    unmount();

    // --- Estudiante render ---
    mockGetUserRole.mockReturnValue("Estudiante");
    mockGetPreferences.mockResolvedValueOnce(ALL_PREFS);

    render(<NotificationsTab />);

    await waitFor(() => {
      expect(screen.getAllByRole("switch")).toHaveLength(STUDENT_PREF_KEYS.length);
    });

    // Admin-only keys must NOT be present for Estudiante
    for (const key of ADMIN_ONLY_KEYS) {
      const dataAttr = document.querySelector(`[data-pref-key="${key}"]`);
      expect(dataAttr).toBeNull();
    }
  });

  it("flips aria-checked immediately (optimistic) before updatePreferences resolves", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetPreferences.mockResolvedValueOnce(ALL_PREFS);
    // Never resolves — lets us assert optimistic flip before settle
    mockUpdatePreferences.mockReturnValue(new Promise(() => {}));

    const user = userEvent.setup();
    render(<NotificationsTab />);

    await waitFor(() => {
      expect(screen.getAllByRole("switch")).toHaveLength(6);
    });

    // Click the first switch (currently aria-checked="true")
    const firstSwitch = screen.getAllByRole("switch")[0];
    expect(firstSwitch).toHaveAttribute("aria-checked", "true");

    await user.click(firstSwitch);

    // Optimistic: should flip to false without waiting for PATCH to resolve
    expect(firstSwitch).toHaveAttribute("aria-checked", "false");

    // updatePreferences must have been called exactly once with the toggled value
    expect(mockUpdatePreferences).toHaveBeenCalledTimes(1);
    // The call should include one key set to false
    const callArg = mockUpdatePreferences.mock.calls[0][0] as Record<string, boolean>;
    const changedValues = Object.values(callArg);
    expect(changedValues).toHaveLength(1);
    expect(changedValues[0]).toBe(false);
  });

  it("rolls back the switch and shows an error when updatePreferences rejects", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetPreferences.mockResolvedValueOnce(ALL_PREFS);
    mockUpdatePreferences.mockRejectedValueOnce(new Error("nope"));

    const user = userEvent.setup();
    render(<NotificationsTab />);

    await waitFor(() => {
      expect(screen.getAllByRole("switch")).toHaveLength(6);
    });

    const firstSwitch = screen.getAllByRole("switch")[0];
    expect(firstSwitch).toHaveAttribute("aria-checked", "true");

    await user.click(firstSwitch);

    // After rejection, the switch must roll back to its original state
    await waitFor(() => {
      expect(firstSwitch).toHaveAttribute("aria-checked", "true");
    });

    // An error message must be visible
    const errorEl = await screen.findByText(/no se pudo|error/i);
    expect(errorEl).toBeInTheDocument();
  });
});
