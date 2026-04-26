import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import AgregarDocumentoPage from "./page";

vi.mock("./hooks/useDocumentData", () => ({
  useDocumentData: vi.fn(),
}));

vi.mock("./components/DocumentFormNew", () => ({
  default: () => <div data-testid="document-form" />,
}));

vi.mock("./components/AccessDenied", () => ({
  default: () => <div data-testid="access-denied" />,
}));

vi.mock("./components/FormSkeleton", () => ({
  default: () => <div data-testid="form-skeleton" />,
}));

vi.mock("@widgets/header/DashboardHeader", () => ({
  default: ({ pageTitle }: { pageTitle?: string }) => (
    <header data-testid="dashboard-header">{pageTitle}</header>
  ),
}));

import { useDocumentData } from "./hooks/useDocumentData";

const baseData = {
  currentUser: null,
  students: [],
  tutors: [],
  jurados: [],
  partners: [],
  semesters: [],
  defaultSemester: "",
  defaultDocType: "proyecto",
  allowedDocumentTypes: ["proyecto", "tesis"] as const,
  handleSemesterChange: vi.fn(),
};

describe("AgregarDocumentoPage — Sub-H chrome", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("admin: renders hero h1 with 'Registrar', shows document form, no access-denied", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Administrador",
      isStudent: false,
      isStaffReviewer: false,
      isLoaded: true,
    });

    render(<AgregarDocumentoPage />);

    expect(screen.getByRole("heading", { level: 1, name: /registrar/i })).toBeTruthy();
    expect(screen.getByTestId("document-form")).toBeTruthy();
    expect(screen.queryByTestId("access-denied")).toBeNull();
  });

  it("estudiante: renders hero h1 with 'Sube' or 'Subir', shows document form", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Estudiante",
      isStudent: true,
      isStaffReviewer: false,
      isLoaded: true,
    });

    render(<AgregarDocumentoPage />);

    expect(screen.getByRole("heading", { level: 1, name: /sub(e|ir)/i })).toBeTruthy();
    expect(screen.getByTestId("document-form")).toBeTruthy();
    expect(screen.queryByTestId("access-denied")).toBeNull();
  });

  it("tutor: renders AccessDenied, no document form", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Tutor",
      isStudent: false,
      isStaffReviewer: true,
      isLoaded: true,
    });

    render(<AgregarDocumentoPage />);

    expect(screen.getByTestId("access-denied")).toBeTruthy();
    expect(screen.queryByTestId("document-form")).toBeNull();
  });

  it("jurado: renders AccessDenied, no document form", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Jurado",
      isStudent: false,
      isStaffReviewer: true,
      isLoaded: true,
    });

    render(<AgregarDocumentoPage />);

    expect(screen.getByTestId("access-denied")).toBeTruthy();
    expect(screen.queryByTestId("document-form")).toBeNull();
  });

  it("loading state: renders FormSkeleton, no document form", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Administrador",
      isStudent: false,
      isStaffReviewer: false,
      isLoaded: false,
    });

    render(<AgregarDocumentoPage />);

    expect(screen.getByTestId("form-skeleton")).toBeTruthy();
    expect(screen.queryByTestId("document-form")).toBeNull();
  });

  it("main element does not use bg-gray-50 or bg-gray-50/50 class", () => {
    (useDocumentData as ReturnType<typeof vi.fn>).mockReturnValue({
      ...baseData,
      userRole: "Administrador",
      isStudent: false,
      isStaffReviewer: false,
      isLoaded: true,
    });

    const { container } = render(<AgregarDocumentoPage />);

    expect(container.querySelector('main.bg-gray-50')).toBeNull();
    expect(container.querySelector('main[class*="gray-50"]')).toBeNull();
  });
});
