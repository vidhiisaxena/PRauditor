import Link from "next/link";

export default function DocsUnderConstruction() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      <img
        src="\construction.gif"
        alt="Under Construction"
        className="w-32 h-32 mb-6"
      />

      <h1 className="text-4xl font-bold mb-4">Documentation Coming Soon</h1>
      <p className="text-lg text-muted-foreground mb-8">
        Working hard to bring you the documentation for PR Auditor.
      </p>

      <Link
        href="https://pr-auditor.vercel.app/"
        className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition"
      >
        Return to Home Page
      </Link>
    </div>
  );
}
