import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/match(.*)",
  "/waitlist",
  "/thank-you",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/clerk",
  "/api/trpc(.*)",
  "/api/backend(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
