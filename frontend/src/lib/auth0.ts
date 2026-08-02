import "server-only";

import { Auth0Client } from "@auth0/nextjs-auth0/server";
import { NextResponse } from "next/server";

const audience = process.env.AUTH0_AUDIENCE?.trim() || "urn:solarahire:api";
const scope =
  process.env.AUTH0_SCOPE?.trim() ||
  "openid profile email offline_access";

export const auth0 = new Auth0Client({
  authorizationParameters: {
    audience,
    scope,
  },
  signInReturnToPath: "/workspace",
  onCallback: async (error, context) => {
    if (error) {
      const authError = error as Error & {
        code?: unknown;
        cause?: { code?: unknown };
      };
      console.error("Auth0 callback failed", {
        name: authError.name,
        code:
          typeof authError.code === "string" ? authError.code : "unknown_error",
        causeCode:
          typeof authError.cause?.code === "string"
            ? authError.cause.code
            : "unknown_error",
      });
    }

    const baseUrl =
      context.appBaseUrl ??
      process.env.APP_BASE_URL ??
      "http://localhost:3000";
    return NextResponse.redirect(
      new URL(error ? "/auth-error" : "/workspace", baseUrl),
    );
  },
});

export const auth0ApiAudience = audience;
export const auth0ApiScope = scope;
