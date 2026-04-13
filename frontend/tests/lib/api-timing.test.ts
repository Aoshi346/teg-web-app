/**
 * Tests that the `api` client in src/lib/api.ts emits a timing log entry
 * after each call in dev mode (process.env.NODE_ENV !== 'production').
 *
 * These tests exercise the REAL api.ts with fetch mocked via vi.stubGlobal
 * so we can observe side-effects (console.info calls) without hitting a server.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/shared/api/api";

// ---- helpers ----------------------------------------------------------------

function makeFetchMock(status: number, body: unknown = {}) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    headers: new Headers(),
  } as Response);
}

// ---- setup / teardown -------------------------------------------------------

let infoSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  // Spy on console.info fresh before each test
  infoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
  // Ensure we start in dev mode
  vi.stubEnv("NODE_ENV", "development");
});

afterEach(() => {
  infoSpy.mockRestore();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

// ---- tests ------------------------------------------------------------------

describe("api timing instrumentation", () => {
  it("logs duration after successful GET", async () => {
    vi.stubGlobal("fetch", makeFetchMock(200, { result: "ok" }));

    await api.get("/test/");

    expect(infoSpy).toHaveBeenCalled();
    const callArg: string = infoSpy.mock.calls[0][0];
    // Message must mention the method and path
    expect(callArg).toMatch(/GET/i);
    expect(callArg).toMatch(/\/test\//);
    // Must include a number (duration in ms)
    expect(callArg).toMatch(/\d+/);
  });

  it("logs duration after POST", async () => {
    vi.stubGlobal("fetch", makeFetchMock(201, { id: 1 }));

    await api.post("/test/", { name: "example" });

    expect(infoSpy).toHaveBeenCalled();
    const callArg: string = infoSpy.mock.calls[0][0];
    expect(callArg).toMatch(/POST/i);
    expect(callArg).toMatch(/\/test\//);
    expect(callArg).toMatch(/\d+/);
  });

  it("logs duration after a failing request", async () => {
    vi.stubGlobal("fetch", makeFetchMock(500, { detail: "Internal server error" }));

    // api.get throws on non-ok responses — catch so test doesn't explode
    try {
      await api.get("/broken/");
    } catch {
      // expected — the api client throws on 5xx
    }

    // Timing log must still fire even when the request fails
    expect(infoSpy).toHaveBeenCalled();
    const callArg: string = infoSpy.mock.calls[0][0];
    // Log must mention the status code so devs can see the failure context
    expect(callArg).toMatch(/500/);
  });

  it("does not log in production", async () => {
    vi.stubGlobal("fetch", makeFetchMock(200, {}));
    // Override NODE_ENV to production for this test only
    vi.stubEnv("NODE_ENV", "production");

    try {
      await api.get("/test/");
    } catch {
      // ignore any errors from the call itself
    }

    expect(infoSpy).not.toHaveBeenCalled();
  });
});
