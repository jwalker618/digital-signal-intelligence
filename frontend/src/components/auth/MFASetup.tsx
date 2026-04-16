// A-3c: MFA enrolment wizard (TOTP QR + backup codes).
//
// Used from the /profile page. Flow:
//   1. GET secret + otpauth URI via /auth/mfa/setup
//   2. User scans QR in authenticator app
//   3. User enters 6-digit code to verify (/auth/mfa/verify)
//   4. On success, backup codes are generated and shown exactly once.
//      The user must acknowledge they've stored them before dismissing.

"use client";

import { FormEvent, useState } from "react";
import { Download, KeyRound, Loader2, ShieldCheck } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { mfaBackupCodes, mfaSetup, mfaVerify } from "@/lib/authApi";

type Stage = "idle" | "qr" | "verifying" | "backup-codes" | "done";

export function MFASetup({ onDone }: { onDone?: () => void }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [stage, setStage] = useState<Stage>("idle");
  const [secret, setSecret] = useState<string | null>(null);
  const [otpauthUri, setOtpauthUri] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [acknowledged, setAcknowledged] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function beginSetup() {
    if (!accessToken) return;
    setBusy(true);
    setError(null);
    try {
      const resp = await mfaSetup(accessToken);
      setSecret(resp.secret);
      setOtpauthUri(resp.otpauth_uri);
      setStage("qr");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setBusy(false);
    }
  }

  async function verify(e: FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    if (!/^\d{6}$/.test(code)) {
      setError("Code must be 6 digits");
      return;
    }
    setBusy(true);
    setError(null);
    setStage("verifying");
    try {
      await mfaVerify(accessToken, code);
      const codes = await mfaBackupCodes(accessToken);
      setBackupCodes(codes.codes);
      setStage("backup-codes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
      setStage("qr");
    } finally {
      setBusy(false);
    }
  }

  function downloadCodes() {
    const blob = new Blob(
      [
        "DSI MFA Backup Codes\n\n" +
          "Each code can be used once if you lose access to your authenticator app.\n\n" +
          backupCodes.map((c, i) => `${i + 1}. ${c}`).join("\n"),
      ],
      { type: "text/plain" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "dsi-backup-codes.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  function finish() {
    setStage("done");
    onDone?.();
  }

  // Build a QR code URL via a text-to-QR image service isn't desirable
  // (leaks secrets). Instead, render the otpauth URI as a copyable
  // string + a basic <canvas>-free guidance box; a dedicated QR lib
  // is out of scope for this phase.
  return (
    <div className="flex flex-col gap-4 border-2 border-dsi-outline rounded p-4">
      <header className="flex items-center gap-2 text-dsi-selected">
        <ShieldCheck className="icon" />
        <span className="font-semibold tracking-wider">
          Two-Factor Authentication
        </span>
      </header>

      {stage === "idle" && (
        <>
          <p className="text-sm opacity-80">
            Protect your account with an authenticator app (Google
            Authenticator, 1Password, Authy, etc).
          </p>
          <button
            onClick={beginSetup}
            disabled={busy}
            className="self-start bg-dsi-contrast-background text-dsi-background py-2 px-4 rounded font-semibold disabled:opacity-50"
          >
            {busy ? "Starting…" : "Set up MFA"}
          </button>
        </>
      )}

      {stage === "qr" && otpauthUri && secret && (
        <>
          <p className="text-sm opacity-80">
            Scan this URI in your authenticator app, or enter the secret
            manually. Then enter the 6-digit code to confirm.
          </p>
          <div className="bg-dsi-background border-2 border-dsi-outline rounded p-3 font-mono text-xs break-all">
            {otpauthUri}
          </div>
          <div className="text-xs opacity-70">
            Secret:{" "}
            <span className="font-mono tracking-widest">{secret}</span>
          </div>
          <form onSubmit={verify} className="flex items-center gap-2">
            <input
              autoFocus
              value={code}
              onChange={(e) =>
                setCode(e.target.value.replace(/\D/g, "").slice(0, 6))
              }
              inputMode="numeric"
              maxLength={6}
              className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 font-mono text-xl tracking-[0.3em] text-center rounded w-40"
              placeholder="000000"
            />
            <button
              type="submit"
              disabled={busy || code.length !== 6}
              className="bg-dsi-contrast-background text-dsi-background py-2 px-4 rounded font-semibold disabled:opacity-50"
            >
              {busy ? <Loader2 className="icon animate-spin" /> : "Verify"}
            </button>
          </form>
        </>
      )}

      {stage === "backup-codes" && (
        <>
          <div className="flex items-center gap-2 text-dsi-selected">
            <KeyRound className="icon" />
            <span className="font-semibold">Save your backup codes</span>
          </div>
          <p className="text-sm opacity-80">
            Each code can be used once if you lose access to your
            authenticator. They are shown exactly once -- save them now.
          </p>
          <ul className="grid grid-cols-2 gap-2 font-mono text-sm">
            {backupCodes.map((c) => (
              <li
                key={c}
                className="border border-dsi-outline/40 bg-dsi-background px-2 py-1 rounded text-center"
              >
                {c}
              </li>
            ))}
          </ul>
          <button
            onClick={downloadCodes}
            className="self-start border-2 border-dsi-outline py-1 px-3 rounded flex items-center gap-2"
          >
            <Download className="icon" /> Download as .txt
          </button>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
            />
            I have saved my backup codes
          </label>
          <button
            disabled={!acknowledged}
            onClick={finish}
            className="self-start bg-dsi-contrast-background text-dsi-background py-2 px-4 rounded font-semibold disabled:opacity-50"
          >
            Done
          </button>
        </>
      )}

      {stage === "done" && (
        <p className="text-sm text-dsi-selected">
          MFA is now enabled on your account.
        </p>
      )}

      {error && <div className="text-sm text-dsi-negative">{error}</div>}
    </div>
  );
}
