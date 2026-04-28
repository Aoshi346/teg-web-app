import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const gsapMocks = vi.hoisted(() => {
  const timeline = vi.fn();
  const set = vi.fn();
  const to = vi.fn();
  const from = vi.fn();
  const context = vi.fn((fn: () => void) => {
    fn();
    return { revert: () => {} };
  });
  return { timeline, set, to, from, context };
});
const { timeline: gsapTimeline, set: gsapSet, to: gsapTo, context: gsapContext } = gsapMocks;

vi.mock("gsap", () => {
  const tl = {
    to: vi.fn().mockReturnThis(),
    from: vi.fn().mockReturnThis(),
    fromTo: vi.fn().mockReturnThis(),
    set: vi.fn().mockReturnThis(),
    add: vi.fn().mockReturnThis(),
  };
  gsapMocks.timeline.mockImplementation(() => tl);
  return {
    gsap: {
      timeline: gsapMocks.timeline,
      set: gsapMocks.set,
      to: gsapMocks.to,
      from: gsapMocks.from,
      context: gsapMocks.context,
    },
  };
});

vi.mock("split-type", () => {
  return {
    default: class {
      lines: HTMLElement[] = [];
      revert() {}
    },
  };
});

const mockMatchMedia = (reducedMotion: boolean) => {
  const mql = (query: string) => ({
    matches: query.includes("prefers-reduced-motion") ? reducedMotion : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  });
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation(mql),
  });
};

import Hero from "../Hero";

describe("Hero — Landing redesign v2026", () => {
  beforeEach(() => {
    gsapTimeline.mockClear();
    gsapSet.mockClear();
    gsapTo.mockClear();
    gsapContext.mockClear();
    mockMatchMedia(false);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("does not render the badge text", () => {
    render(<Hero />);
    expect(screen.queryByText(/Plataforma de Gestión Académica/i)).toBeNull();
  });

  it("does not render fase pulse or corner mark", () => {
    const { container } = render(<Hero />);
    expect(container.querySelector('[data-testid="fase-pulse"]')).toBeNull();
    expect(container.querySelector(".lh-corner-mark")).toBeNull();
  });

  it("does not render the floating CSS blob containers", () => {
    const { container } = render(<Hero />);
    const blobs = container.querySelectorAll(
      '[class*="bg-usm-blue/10"], [class*="bg-usm-orange/10"]'
    );
    expect(blobs.length).toBe(0);
  });

  it("renders the stacked-layered pair without Vol II label", () => {
    const { container } = render(<Hero />);
    const pair = container.querySelector('[data-testid="hero-stack-pair"]');
    expect(pair).not.toBeNull();
    expect(pair!.querySelectorAll(".lh-stack-sub").length).toBe(1);
    expect(pair!.querySelectorAll(".lh-stack-secondary").length).toBe(1);
    expect(screen.queryByText(/Vol II/i)).toBeNull();
  });

  it("preserves the verbatim Spanish sub paragraph", () => {
    const { container } = render(<Hero />);
    const sub = container.querySelector(".lh-stack-sub");
    expect(sub).not.toBeNull();
    const text = sub!.textContent || "";
    expect(text).toContain("Centraliza");
    expect(text).toContain("recordatorios automáticos");
    expect(text).toContain("comités.");
  });

  it("preserves the secondary copy", () => {
    const { container } = render(<Hero />);
    const sec = container.querySelector(".lh-stack-secondary");
    expect(sec).not.toBeNull();
    expect(sec!.textContent).toContain(
      "Coordina a estudiantes, tutores y jurados con comunicación fluida."
    );
  });

  it("renders two stamp CTAs with the correct labels and numeral", () => {
    const { container } = render(<Hero />);
    const primary = container.querySelector(".lh-btn-stamp");
    const ghost = container.querySelector(".lh-btn-stamp-ghost");
    expect(primary).not.toBeNull();
    expect(ghost).not.toBeNull();
    const num = primary!.querySelector(".lh-btn-num");
    expect(num).not.toBeNull();
    expect(num!.textContent).toBe("01");
    expect(primary!.textContent).toContain("Comenzar ahora");
    expect(ghost!.textContent).toContain("Ver funciones");
  });

  it("renders the bridge pill instead of a ChevronDown icon", () => {
    const { container } = render(<Hero />);
    const pill = container.querySelector(".lh-bridge-pill");
    expect(pill).not.toBeNull();
    expect(pill!.getAttribute("aria-label")).not.toBeNull();
    expect(pill!.textContent).toContain("Cómo te ayuda Tesisfar");
    expect(container.querySelector(".lucide-chevron-down")).toBeNull();
  });

  it("does not build the GSAP timeline under prefers-reduced-motion", () => {
    mockMatchMedia(true);
    render(<Hero />);
    expect(gsapTimeline).not.toHaveBeenCalled();
  });

  it("primary CTA delegates to the hidden Ingresar button", () => {
    const hidden = document.createElement("button");
    hidden.setAttribute("aria-label", "Ingresar");
    const clickSpy = vi.fn();
    hidden.addEventListener("click", clickSpy);
    document.body.appendChild(hidden);

    const { container } = render(<Hero />);
    const primary = container.querySelector(".lh-btn-stamp") as HTMLButtonElement;
    fireEvent.click(primary);
    expect(clickSpy).toHaveBeenCalled();
    document.body.removeChild(hidden);
  });

  it("ghost CTA and bridge pill scroll to #features", () => {
    const fakeFeatures = document.createElement("div");
    fakeFeatures.id = "features";
    const scrollSpy = vi.fn();
    fakeFeatures.scrollIntoView = scrollSpy;
    document.body.appendChild(fakeFeatures);

    const { container } = render(<Hero />);
    const ghost = container.querySelector(".lh-btn-stamp-ghost") as HTMLButtonElement;
    fireEvent.click(ghost);
    expect(scrollSpy).toHaveBeenCalled();

    const pill = container.querySelector(".lh-bridge-pill") as HTMLButtonElement;
    fireEvent.click(pill);
    expect(scrollSpy).toHaveBeenCalledTimes(2);

    document.body.removeChild(fakeFeatures);
  });
});
