import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AccessDenied from "./AccessDenied";

// next/navigation is globally mocked in vitest.setup.ts (useRouter with back/push/etc.)
// next/link is NOT globally mocked — the component must render a real anchor.
// We rely on jsdom rendering <a href="..."> from next/link naturally in test env.

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

describe("AccessDenied — Sub-H polish", () => {
  it("renders a heading with text indicating unavailability or restriction", () => {
    render(<AccessDenied />);

    const heading = screen.getByRole("heading");
    expect(heading).toBeTruthy();
    expect(heading.textContent?.toLowerCase()).toMatch(/no está disponible|restringid/i);
  });

  it("'Ir a Seguimiento' link points to /dashboard/tracking", () => {
    render(<AccessDenied />);

    const link = screen.getByRole("link", { name: /seguimiento/i });
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toBe("/dashboard/tracking");
  });

  it("'Volver' button is present", () => {
    render(<AccessDenied />);

    expect(screen.getByRole("button", { name: /volver/i })).toBeTruthy();
  });

  it("renders the .agg-denied wrapper class", () => {
    const { container } = render(<AccessDenied />);

    expect(container.querySelector(".agg-denied")).not.toBeNull();
  });

  it("does NOT render raw bg-amber-50 or border-amber-200 classes", () => {
    const { container } = render(<AccessDenied />);

    expect(container.querySelector(".bg-amber-50")).toBeNull();
    expect(container.querySelector(".border-amber-200")).toBeNull();
  });
});
