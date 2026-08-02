// @vitest-environment node

import { describe, expect, it, vi } from "vitest";

import {
  attachSessionHeaders,
  resolveApiIdentity,
} from "@/lib/auth/session";

type AuthClient = NonNullable<Parameters<typeof resolveApiIdentity>[1]>;

describe("server-side Auth0 session transport", () => {
  it("keeps anonymous requests anonymous without consulting Auth0", async () => {
    const client = {
      getSession: vi.fn(),
      getAccessToken: vi.fn(),
    } as unknown as AuthClient;

    const identity = await resolveApiIdentity(
      new Request("http://localhost/api/resumes/parse"),
      client,
    );

    expect(identity.authorization).toBeNull();
    expect(client.getSession).not.toHaveBeenCalled();
    expect(client.getAccessToken).not.toHaveBeenCalled();
  });

  it("returns a server-only bearer token for an authenticated session", async () => {
    const client = {
      getSession: vi.fn().mockResolvedValue({ user: { sub: "auth0|ada" } }),
      getAccessToken: vi.fn().mockResolvedValue({
        token: "signed-api-token",
        expiresAt: 2_000_000_000,
      }),
    } as unknown as AuthClient;

    const identity = await resolveApiIdentity(
      new Request("http://localhost/api/resumes/parse", {
        headers: { cookie: "__session=encrypted" },
      }),
      client,
    );

    expect(identity.authorization).toBe("Bearer signed-api-token");
    expect(client.getAccessToken).toHaveBeenCalledOnce();
  });

  it("copies rotated session cookies onto the route response", () => {
    const sessionHeaders = new Headers();
    sessionHeaders.append(
      "set-cookie",
      "__session=rotated; Path=/; HttpOnly; SameSite=Lax",
    );

    const response = attachSessionHeaders(Response.json({ ok: true }), {
      authorization: "Bearer signed-api-token",
      sessionHeaders,
    });

    expect(response.headers.get("set-cookie")).toContain("__session=rotated");
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
  });
});
