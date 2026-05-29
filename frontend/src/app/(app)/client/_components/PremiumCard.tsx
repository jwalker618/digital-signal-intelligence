import { memo } from "react";
import { Card } from "@/components/ui/card";
import { Eyebrow, NumDisplay, Body, Caption } from "@/components/ui/typography";
import { PremiumBreakdown, type PremiumSlice } from "@/components/charts/premium-breakdown";
import { formatCurrency } from "@/lib/format";

export const PremiumCard = memo(function PremiumCard({
  slices,
  fallbackTotal,
}: {
  slices: PremiumSlice[];
  fallbackTotal: number | null;
}) {
  const total = slices.reduce((s, p) => s + p.amount, 0) || fallbackTotal || 0;
  const count = slices.length;
  return (
    <Card pad="lg" className="flex flex-col">
      <Eyebrow>Annual premium</Eyebrow>
      <NumDisplay size="xl" className="mt-2">
        {total > 0 ? formatCurrency(total) : "—"}
      </NumDisplay>
      {count > 0 && (
        <Caption className="mt-1">
          Across {count} active polic{count === 1 ? "y" : "ies"}
        </Caption>
      )}
      <div className="mt-auto pt-4">
        {slices.length > 0 ? (
          <PremiumBreakdown slices={slices} maxVisible={4} />
        ) : (
          <Body className="italic">No priced coverages yet.</Body>
        )}
      </div>
    </Card>
  );
});
