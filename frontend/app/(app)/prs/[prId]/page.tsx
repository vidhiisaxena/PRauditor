import { notFound } from "next/navigation";

import { ReviewDetailView } from "@/components/reviews/ReviewDetailView";

export default function ReviewDetailPage({
  params,
}: {
  params: { prId: string };
}) {
  const prId = Number(params.prId);
  if (!Number.isInteger(prId)) notFound();

  return <ReviewDetailView prId={prId} />;
}
