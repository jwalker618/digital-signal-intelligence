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
import { 
  Download, 
  KeyRound, 
  Loader2, 
  ShieldCheck 
} from "lucide-react";

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
    a.download = "generate-backup-codes.txt";
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
    
    <div className="flex flex-col">

      {stage === "idle" && (
        <>
          <p className="text-xs pb-2">
            Protect your account with an authenticator app (Google
            Authenticator, etc).
          </p>
          
          <button
            onClick={beginSetup}
            disabled={busy}
            className="generate-actionbutton"
          >
            {busy ? "Starting…" : "Set up MFA"}
          </button>
        </>
      )}

      {stage === "qr" && otpauthUri && secret && (
        <>
          
          <p className="text-xs pb-2">
            Scan this URI in your authenticator app, or enter the secret
            manually. Then enter the 6-digit code to confirm.
          </p>
          
          <div className="generate-notificationpill wrap-anywhere border-none">
            {otpauthUri}
          </div>

          <p className="text-xs pt-2 pb-2">
            Secret:{" "}
          </p>          

          <div className="generate-notificationpill wrap-anywhere border-none">
            {secret}
          </div>

          <form onSubmit={verify} className="flex flex-col pt-2 pb-2 gap-2">
            <input
              autoFocus
              value={code}
              onChange={(e) =>
                setCode(e.target.value.replace(/\D/g, "").slice(0, 6))
              }
              inputMode="numeric"
              maxLength={6}
              className="generate-inputbox text-right"
              placeholder="000000"
            />
            
            <button
              type="submit"
              disabled={busy || code.length !== 6}
              className="generate-actionbutton"
            >
              {busy ? <Loader2 className="icon animate-spin" /> : "Verify"}
            </button>

          </form>
        </>
      )}

      {stage === "backup-codes" && (
        <>
          
          <div className="flex items-center gap-2 text-generate-selected">
            <KeyRound className="icon" />
            <span className="font-semibold">Save your backup codes</span>
          </div>
          
          <p className="text-xs pb-2">
            Each code can be used once if you lose access to your
            authenticator. They are shown exactly once -- save them now.
          </p>
          
          <ul className="grid grid-cols-2 gap-2">
            {backupCodes.map((c) => (
              <li
                key={c}
                className="
                  generate-analysis-item 
                  font-normal text-xs p-1.5
                  border-r border-b border-generate-outline 
                  rounded-sm"
              >
                {c}
              </li>
            ))}
          </ul>
          
          <button
            onClick={downloadCodes}
            className="generate-actionbutton"
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
            className="generate-actionbutton"
          >Done
          </button>
        </>
      )}

      {stage === "done" && (
        <p className="text-sm text-generate-selected">
          MFA is now enabled on your account.
        </p>
      )}

      {error && <div className="generate-user-message text-left">{error}</div>}
    </div>
  );
}
