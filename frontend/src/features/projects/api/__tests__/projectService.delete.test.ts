import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@shared/api/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  postForm: vi.fn(),
}));

import { api } from "@shared/api/api";
import { deleteProject } from "../projectService";

const mockApiDelete = vi.mocked(api.delete);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("deleteProject", () => {
  it("issues DELETE /projects/{id}/ via the api client", async () => {
    mockApiDelete.mockResolvedValueOnce({} as void);
    await deleteProject(99);
    expect(mockApiDelete).toHaveBeenCalledWith("/projects/99/");
  });

  it("resolves with no meaningful body on 204 (api returns {})", async () => {
    mockApiDelete.mockResolvedValueOnce({} as void);
    const result = await deleteProject(5);
    expect(result).toBeUndefined();
  });

  it("rejects with the error from api on non-2xx", async () => {
    mockApiDelete.mockRejectedValueOnce(new Error("Not found"));
    await expect(deleteProject(404)).rejects.toThrow("Not found");
  });
});
