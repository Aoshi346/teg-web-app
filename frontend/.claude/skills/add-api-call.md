---
name: add-api-call
description: Add a new API service function with proper typing and CSRF handling
user_invocable: true
arguments:
  - name: endpoint
    description: The Django API endpoint path (e.g., "/reports/", "/users/{id}/stats/")
    required: true
  - name: method
    description: "HTTP method: GET, POST, PATCH, PUT, or DELETE"
    required: true
  - name: service
    description: "Which service file to add it to: auth (clientAuth.ts) or projects (projectService.ts), or 'new' to create a new service"
    required: false
---

# Add API Call

Add a new API service function to TesisFar's frontend, connecting to the Django backend.

## Steps

1. **Determine the service file**:
   - Auth/user operations → `src/features/auth/clientAuth.ts`
   - Project/evaluation/semester/comment operations → `src/features/projects/projectService.ts`
   - If `{{ service }}` is "new", create `src/features/<domain>/<domain>Service.ts`

2. **Define TypeScript types** in `src/types/project.ts` (or a new types file if the domain is unrelated to projects):
   - Create request payload interface if POST/PUT/PATCH
   - Create response interface for the returned data
   - Follow existing naming: PascalCase, descriptive names

3. **Add the service function** following this pattern:

   ```typescript
   // For JSON requests — use the api client from @/lib/api
   import { api } from "@/lib/api";

   // GET request
   export async function getThings(): Promise<Thing[]> {
     return api.get<Thing[]>("/things/");
   }

   // POST request
   export async function createThing(data: CreateThingPayload): Promise<Thing> {
     return api.post<Thing>("/things/", data);
   }

   // PATCH request
   export async function updateThing(id: number, data: Partial<Thing>): Promise<Thing> {
     return api.patch<Thing>(`/things/${id}/`, data);
   }

   // DELETE request
   export async function deleteThing(id: number): Promise<void> {
     return api.delete<void>(`/things/${id}/`);
   }

   // For file uploads — use postForm from @/lib/api
   import { postForm } from "@/lib/api";

   export async function uploadFile(id: number, file: File): Promise<FileResponse> {
     const formData = new FormData();
     formData.append("file", file);
     return postForm<FileResponse>(`/things/${id}/files/`, formData);
   }
   ```

4. **Key conventions**:
   - The `api` client automatically handles CSRF tokens and session cookies
   - All endpoints are relative to `http://localhost:8000/api` (configured in `lib/api.ts`)
   - Django endpoints always end with a trailing slash `/`
   - Use `postForm()` for multipart/form-data uploads (it skips JSON Content-Type)
   - Error handling is built into the api client — it throws `Error` with the server message

5. **Do NOT**:
   - Use `fetch()` directly — always use the `api` client or `postForm`
   - Hardcode the API base URL — it's defined in `lib/api.ts` as `API_URL`
   - Add redundant CSRF handling — the api client does this automatically
