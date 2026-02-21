import { headers } from "next/headers";
import { Webhook } from "svix";
import type { WebhookEvent } from "@clerk/nextjs/server";
import { clerkClient } from "@clerk/nextjs/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;
  if (!WEBHOOK_SECRET) {
    return new Response("Webhook secret not configured", { status: 500 });
  }

  const headerPayload = await headers();
  const svix_id = headerPayload.get("svix-id");
  const svix_timestamp = headerPayload.get("svix-timestamp");
  const svix_signature = headerPayload.get("svix-signature");

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response("Missing svix headers", { status: 400 });
  }

  const payload = await req.json();
  const body = JSON.stringify(payload);

  const wh = new Webhook(WEBHOOK_SECRET);
  let evt: WebhookEvent;

  try {
    evt = wh.verify(body, {
      "svix-id": svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    }) as WebhookEvent;
  } catch {
    return new Response("Invalid webhook signature", { status: 400 });
  }

  if (evt.type === "user.created") {
    const { id, email_addresses, first_name, last_name } = evt.data;
    const email = email_addresses?.[0]?.email_address || "";
    const name = [first_name, last_name].filter(Boolean).join(" ");

    try {
      // Sync user to FastAPI backend
      const syncRes = await fetch(`${API_BASE}/auth/sync-user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clerk_user_id: id,
          email,
          name,
        }),
      });

      if (syncRes.ok) {
        const { user_id } = await syncRes.json();

        // Store user_id in Clerk public metadata
        const client = await clerkClient();
        await client.users.updateUserMetadata(id, {
          publicMetadata: { user_id },
        });
      }

      // Send welcome email via Resend
      const resendKey = process.env.RESEND_API_KEY;
      if (resendKey && email) {
        await fetch("https://api.resend.com/emails", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${resendKey}`,
          },
          body: JSON.stringify({
            from: "PRELUDE <hello@prelude.app>",
            to: email,
            subject: "You're on the list.",
            html: `<div style="font-family: monospace; color: #e8f4ff; background: #020408; padding: 40px; max-width: 480px;">
              <p style="font-size: 16px; line-height: 1.6;">PRELUDE simulates 100+ futures of your relationship — the fights, the growth, the breaking points — so you know what you're walking into.</p>
              <p style="font-size: 16px; line-height: 1.6;">Next step: complete your shadow vector profile. It takes 3 minutes.</p>
              <p style="margin-top: 24px;"><a href="${process.env.FRONTEND_URL || "https://prelude.app"}/onboarding" style="color: #00c8ff; font-size: 16px;">Complete your profile &rarr;</a></p>
            </div>`,
          }),
        });
      }
    } catch (error) {
      console.error("Webhook user.created handler error:", error);
    }

    return new Response("OK", { status: 200 });
  }

  if (evt.type === "user.deleted") {
    const { id } = evt.data;

    try {
      await fetch(`${API_BASE}/auth/users/${id}/soft-delete`, {
        method: "POST",
      });
    } catch (error) {
      console.error("Webhook user.deleted handler error:", error);
    }

    return new Response("OK", { status: 200 });
  }

  return new Response("Unhandled event type", { status: 200 });
}
