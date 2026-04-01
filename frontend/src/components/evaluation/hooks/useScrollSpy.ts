import { useState, useEffect, useCallback } from "react";

export function useScrollSpy(prefix = "subsection-") {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    const handler = (entries: IntersectionObserverEntry[]) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target.id?.startsWith(prefix)) {
        setActiveId(visible.target.id.replace(prefix, ""));
      }
    };

    const observer = new IntersectionObserver(handler, {
      root: null,
      rootMargin: "-10% 0px -40% 0px",
      threshold: [0.25, 0.5, 0.75],
    });

    const nodes = document.querySelectorAll(`[id^="${prefix}"]`);
    nodes.forEach((n) => observer.observe(n));
    return () => observer.disconnect();
  }, [prefix]);

  const scrollTo = useCallback((sub: string) => {
    const el = document.getElementById(`${prefix}${sub}`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [prefix]);

  return { activeId, scrollTo };
}
