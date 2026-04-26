import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ScoreGauge } from "./ScoreGauge";

describe("ScoreGauge", () => {
  it("renders the score value", () => {
    const { getByText } = render(<ScoreGauge score={18.4} />);
    expect(getByText("18.4")).toBeTruthy();
  });

  it("computes percentage out of max=20 by default", () => {
    const { container } = render(<ScoreGauge score={15} />);
    const el = container.firstChild as HTMLElement;
    expect(el.style.getPropertyValue("--pct")).toBe("75");
  });

  it("clamps percentage to [0, 100]", () => {
    const { container: low } = render(<ScoreGauge score={-2} />);
    expect((low.firstChild as HTMLElement).style.getPropertyValue("--pct")).toBe("0");
    const { container: high } = render(<ScoreGauge score={42} />);
    expect((high.firstChild as HTMLElement).style.getPropertyValue("--pct")).toBe("100");
  });

  it("supports a custom max", () => {
    const { container } = render(<ScoreGauge score={50} max={100} />);
    expect((container.firstChild as HTMLElement).style.getPropertyValue("--pct")).toBe("50");
  });

  it("size variants apply class modifiers", () => {
    const { container: sm } = render(<ScoreGauge score={10} size="sm" />);
    expect((sm.firstChild as HTMLElement).className).toContain("gauge-sm");
    const { container: lg } = render(<ScoreGauge score={10} size="lg" />);
    expect((lg.firstChild as HTMLElement).className).toContain("gauge-lg");
  });

  it("tone='success' uses gauge-green class", () => {
    const { container } = render(<ScoreGauge score={18} tone="success" />);
    expect((container.firstChild as HTMLElement).className).toContain("gauge-green");
  });

  it("formats integer scores without decimal", () => {
    const { getByText } = render(<ScoreGauge score={18} />);
    expect(getByText("18")).toBeTruthy();
  });

  it("formats one-decimal scores precisely", () => {
    const { getByText } = render(<ScoreGauge score={17.6} />);
    expect(getByText("17.6")).toBeTruthy();
  });
});
