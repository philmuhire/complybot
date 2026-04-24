import { SignUpView } from "./SignUpView";

/** Required for `output: "export"`: pre-render the default sign-up path. */
export function generateStaticParams() {
  return [{ "sign-up": [] as const }];
}

export default function SignUpPage() {
  return <SignUpView />;
}
