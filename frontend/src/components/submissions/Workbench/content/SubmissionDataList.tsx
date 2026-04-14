"use client";

/**
 * Modal body — raw submission data key/value list (excl. limit, product_type).
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatText } from "@/lib/format";
import KeyValueList from "@/components/base/keyValueList";

const HIDDEN_KEYS = new Set(["limit", "product_type"]);

export default function SubmissionDataList() {
  const { activeSubmission } = useDsiStore() as any;

  return (
    <KeyValueList
      data={activeSubmission?.submission_data}
      filter={(k) => !HIDDEN_KEYS.has(k)}
      renderLabel={(k) => formatText(k, "normal")}
      renderValue={(val, key) =>
        typeof val === "number" && key.toLowerCase().includes("revenue")
          ? `$${val.toLocaleString()}`
          : String(val)
      }
      emptyMessage="No submission data available."
    />
  );
}
