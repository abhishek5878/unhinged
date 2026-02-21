import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export const runtime = "edge";

const attachmentLabels: Record<string, string> = {
  anxious: "Anxiously Attached",
  avoidant: "Avoidant",
  secure: "Securely Attached",
  fearful: "Fearful-Avoidant",
};

const attachmentReads: Record<string, string> = {
  anxious: "You love deeply and need to know it's reciprocated.",
  avoidant: "You protect your inner world fiercely.",
  secure: "You can hold space without losing yourself.",
  fearful: "You want depth but fear what it costs.",
};

const valueLabels: Record<string, string> = {
  autonomy: "Freedom",
  security: "Security",
  achievement: "Achievement",
  intimacy: "Depth",
  novelty: "Adventure",
  stability: "Stability",
  power: "Influence",
  belonging: "Belonging",
};

export async function GET(
  req: NextRequest,
  { params }: { params: { userId: string } }
) {
  const { userId } = params;
  const format = req.nextUrl.searchParams.get("format") ?? "og"; // "og" | "square"

  const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  // Fetch shadow vector from backend (public profile endpoint)
  let attachmentStyle = "secure";
  let topValues: string[] = ["Freedom", "Depth", "Security"];

  try {
    const res = await fetch(`${API}/profiles/${userId}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) {
      const data = await res.json();
      const sv = data.shadow_vector ?? {};
      attachmentStyle = sv.attachment_style ?? "secure";
      const valueMap: Record<string, number> = sv.values ?? {};
      topValues = Object.entries(valueMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([k]) => valueLabels[k] ?? k);
    }
  } catch {
    // use defaults
  }

  const isSquare = format === "square";
  const width = isSquare ? 1080 : 1200;
  const height = isSquare ? 1080 : 630;

  const label = attachmentLabels[attachmentStyle] ?? "Profiled";
  const read = attachmentReads[attachmentStyle] ?? "";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#020408",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: isSquare ? "80px" : "60px 80px",
          fontFamily: "monospace",
          position: "relative",
        }}
      >
        {/* Subtle gradient overlay */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(ellipse 80% 60% at 20% 30%, rgba(0,200,255,0.05) 0%, transparent 70%)",
          }}
        />

        {/* PRELUDE badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div
            style={{
              border: "1px solid rgba(0,200,255,0.3)",
              borderRadius: "999px",
              padding: "6px 16px",
              display: "flex",
            }}
          >
            <span
              style={{
                color: "rgba(0,200,255,0.8)",
                fontSize: "11px",
                letterSpacing: "0.25em",
                textTransform: "uppercase",
              }}
            >
              PRELUDE
            </span>
          </div>
          <span
            style={{
              color: "rgba(232,244,255,0.2)",
              fontSize: "11px",
              letterSpacing: "0.15em",
            }}
          >
            SHADOW VECTOR
          </span>
        </div>

        {/* Core content */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Top values */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {topValues.map((v, i) => (
              <span
                key={v}
                style={{
                  color: "#e8f4ff",
                  fontSize: `${isSquare ? 64 - i * 10 : 52 - i * 8}px`,
                  fontWeight: "800",
                  lineHeight: 1,
                  opacity: 1 - i * 0.15,
                }}
              >
                {v}
              </span>
            ))}
          </div>

          {/* Divider */}
          <div
            style={{
              width: "60px",
              height: "2px",
              background: "rgba(0,200,255,0.4)",
            }}
          />

          {/* Attachment label + read */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <span
              style={{
                color: "#00c8ff",
                fontSize: isSquare ? "22px" : "18px",
                letterSpacing: "0.05em",
                fontWeight: "600",
              }}
            >
              {label}
            </span>
            <span
              style={{
                color: "rgba(232,244,255,0.5)",
                fontSize: isSquare ? "18px" : "15px",
                lineHeight: 1.5,
                maxWidth: "540px",
              }}
            >
              {read}
            </span>
          </div>
        </div>

        {/* Footer */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <span
            style={{
              color: "rgba(232,244,255,0.2)",
              fontSize: "12px",
              letterSpacing: "0.1em",
            }}
          >
            prelude.app
          </span>
          <span
            style={{
              color: "rgba(232,244,255,0.15)",
              fontSize: "11px",
              letterSpacing: "0.05em",
            }}
          >
            See the relationship before the relationship.
          </span>
        </div>
      </div>
    ),
    { width, height }
  );
}
