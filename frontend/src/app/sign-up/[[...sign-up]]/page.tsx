import { SignUp } from "@clerk/nextjs";

const afterSignUp =
  process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL?.trim() ||
  process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL?.trim() ||
  "/Dashboard";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
      <SignUp forceRedirectUrl={afterSignUp} fallbackRedirectUrl={afterSignUp} />
    </div>
  );
}
