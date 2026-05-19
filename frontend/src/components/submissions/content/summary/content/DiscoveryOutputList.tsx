"use client";

/**
 * Modal body — discovery output key/value list.
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatText } from "@/lib/format";
import { KeyValueList } from "@/components/base/content/primatives";

export default function DiscoveryOutputList() {
  const { activeVersion } = useDsiStore() as any;

  return (
    <KeyValueList
      data={activeVersion?.discovery_output}
      renderLabel={(k) => formatText(k, "upper")}
      valueClassName="text-generate-text-placeholder"
      emptyMessage="No discovery output available."
    />
  );
}
