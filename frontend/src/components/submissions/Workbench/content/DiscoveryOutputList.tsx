"use client";

/**
 * Modal body — discovery output key/value list.
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatKey } from "@/lib/format";
import { KeyValueList } from "@/components/base/content/primatives";

export default function DiscoveryOutputList() {
  const { activeVersion } = useDsiStore() as any;

  return (
    <KeyValueList
      data={activeVersion?.discovery_output}
      renderLabel={(k) => formatKey(k)}
      valueClassName="text-dsi-selected"
      emptyMessage="No discovery output available."
    />
  );
}
