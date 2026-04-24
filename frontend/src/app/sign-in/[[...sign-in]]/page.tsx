import { SignInView } from "./SignInView";

/** Required for `output: "export"`: pre-render the default sign-in path. */
export function generateStaticParams() {
  return [{ "sign-in": [] as const }];
}

export default function SignInPage() {
  return <SignInView />;
}
