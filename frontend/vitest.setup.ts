import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

process.env.AUTH0_DOMAIN ??= "identity.example.test";
process.env.AUTH0_CLIENT_ID ??= "test-client";
process.env.AUTH0_CLIENT_SECRET ??= "test-client-secret";
process.env.AUTH0_SECRET ??= "0".repeat(64);
process.env.APP_BASE_URL ??= "http://localhost:3000";
process.env.AUTH0_AUDIENCE ??= "urn:solarahire:api";

afterEach(() => {
  cleanup();
});
