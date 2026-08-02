import "server-only";

import type { User } from "@auth0/nextjs-auth0/types";
import { NextRequest, NextResponse } from "next/server";

import { auth0, auth0ApiAudience, auth0ApiScope } from "@/lib/auth0";

export type SiteUser = {
  subject: string;
  name: string;
  email: string | null;
  emailVerified: boolean;
  picture: string | null;
};

export type ApiIdentity = {
  authorization: string | null;
  sessionHeaders: Headers;
};

type Auth0ServerClient = Pick<
  typeof auth0,
  "getSession" | "getAccessToken"
>;

function toSiteUser(user: User): SiteUser {
  const email = typeof user.email === "string" ? user.email : null;
  const fallbackName = email?.split("@", 1)[0] || "Solara Hire member";

  return {
    subject: user.sub,
    name:
      typeof user.name === "string" && user.name.trim()
        ? user.name
        : fallbackName,
    email,
    emailVerified: user.email_verified === true,
    picture: typeof user.picture === "string" ? user.picture : null,
  };
}

export async function getSiteUser(): Promise<SiteUser | null> {
  const session = await auth0.getSession();
  return session ? toSiteUser(session.user) : null;
}

export async function resolveApiIdentity(
  request: Request,
  client: Auth0ServerClient = auth0,
): Promise<ApiIdentity> {
  if (!request.headers.get("cookie")) {
    return { authorization: null, sessionHeaders: new Headers() };
  }

  const nextRequest = new NextRequest(request.url, {
    headers: request.headers,
    method: request.method,
  });
  const session = await client.getSession(nextRequest);
  if (!session) {
    return { authorization: null, sessionHeaders: new Headers() };
  }

  const sessionResponse = NextResponse.next();
  const { token } = await client.getAccessToken(
    nextRequest,
    sessionResponse,
    {
      audience: auth0ApiAudience,
      scope: auth0ApiScope,
    },
  );

  return {
    authorization: `Bearer ${token}`,
    sessionHeaders: sessionResponse.headers,
  };
}

export function attachSessionHeaders(
  response: Response,
  identity: ApiIdentity,
): Response {
  for (const cookie of identity.sessionHeaders.getSetCookie()) {
    response.headers.append("set-cookie", cookie);
  }
  return response;
}
