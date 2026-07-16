import { notFound } from "next/navigation";

import { RepositoryDetailView } from "@/components/repositories/RepositoryDetailView";

export default function RepositoryDetailPage({
  params,
}: {
  params: { repoId: string };
}) {
  const repoId = Number(params.repoId);
  if (!Number.isInteger(repoId)) notFound();

  return <RepositoryDetailView repoId={repoId} />;
}
