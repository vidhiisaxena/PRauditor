import { AppShell } from "@/components/layout/AppShell";

/** Layout for the app: renders the persistent shell around routed pages. */
export default function AppGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
