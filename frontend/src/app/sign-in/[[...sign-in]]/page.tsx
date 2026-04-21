import { SignIn } from "@clerk/nextjs";

const afterSignIn =
  process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL?.trim() || "/Dashboard";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
      <SignIn forceRedirectUrl={afterSignIn} fallbackRedirectUrl={afterSignIn} />
    </div>
  );
}
