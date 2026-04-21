import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
]);

const postAuthHome =
  process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL?.trim() || "/Dashboard";

export default clerkMiddleware(async (auth, req) => {
  const { userId } = await auth();

  // Signed-in users hitting the marketing homepage → app shell (Clerk often falls back to `/`).
  if (userId && req.nextUrl.pathname === "/") {
    return NextResponse.redirect(new URL(postAuthHome, req.url));
  }

  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
