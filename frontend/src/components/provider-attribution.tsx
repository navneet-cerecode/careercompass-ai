import Image from "next/image";

import type { JobResponse } from "@/lib/api/job-contract";

type ProviderAttributionProps = Pick<
  JobResponse,
  "source" | "source_name" | "source_url"
>;

function adzunaOrigin(sourceUrl: string | null | undefined) {
  try {
    const url = new URL(sourceUrl ?? "");
    return /(^|\.)adzuna\.(com|[a-z]{2}|co\.[a-z]{2})$/.test(url.hostname)
      ? url.origin
      : "https://www.adzuna.com";
  } catch {
    return "https://www.adzuna.com";
  }
}

export function ProviderAttribution({
  source,
  source_name: sourceName,
  source_url: sourceUrl,
}: ProviderAttributionProps) {
  if (source === "The Muse" && sourceUrl) {
    return (
      <a className="job-source" href={sourceUrl} target="_blank" rel="noreferrer">
        {source}
      </a>
    );
  }
  if (source !== "Adzuna") {
    return <span className="job-source">{sourceName ?? source}</span>;
  }

  const href = adzunaOrigin(sourceUrl);
  return (
    <span className="adzuna-attribution" aria-label="Jobs by Adzuna">
      <a href={href} target="_blank" rel="noreferrer">
        Jobs by
      </a>
      <a href={href} target="_blank" rel="noreferrer" aria-label="Adzuna">
        <Image
          src="/providers/adzuna-logo.png"
          alt="Adzuna"
          width={70}
          height={18}
          unoptimized
        />
      </a>
    </span>
  );
}
