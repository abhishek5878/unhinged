import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/match(.*)",
  "/waitlist",
  "/thank-you",
  "/privacy",
  "/terms",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/simulate/invite(.*)",
  "/profile(.*)",
  "/api/webhooks/clerk",
  "/api/trpc(.*)",
  "/api/backend(.*)",
  "/api/shadow-vector(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  // Redirect legacy /app/onboarding path
  if (request.nextUrl.pathname.startsWith("/app/onboarding")) {
    const url = request.nextUrl.clone();
    url.pathname = "/onboarding";
    return NextResponse.redirect(url);
  }

  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
