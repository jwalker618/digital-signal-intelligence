// A-4g: NotificationPreferences panel for the profile page.
//
// Responsibilities:
//   - Request browser permission + register a Web Push subscription
//   - Toggle per-category push/in-app preferences
//   - Send a test notification
//   - Unsubscribe (server + browser)

"use client";

import { useEffect, useMemo, useState } from "react";
import { Bell, BellOff, Loader2, Send } from "lucide-react";

import {
  getPushManager,
  type CategoryPreference,
  type PreferencesMap,
} from "@/lib/push";

const CATEGORY_LABELS: Record<string, string> = {
  referral_pending: "Referrals awaiting my decision",
  referral_decided: "Referrals I submitted were decided",
  assessment_complete: "Assessment finished processing",
  config_deployed: "Config version deployed",
  recalibration_proposed: "New recalibration proposal",
  recalibration_decided: "Proposal I reviewed was decided",
  drift_alert: "World Engine drift alerts",
  concentration_alert: "Portfolio concentration alerts",
};

export function NotificationPreferences() {
  const mgr = useMemo(() => getPushManager(), []);
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>("default");
  const [prefs, setPrefs] = useState<PreferencesMap | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      setSupported(await mgr.isSupported());
      if (typeof Notification !== "undefined") {
        setPermission(Notification.permission);
      }
      try {
        setPrefs(await mgr.getPreferences());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load preferences");
      }
    })();
  }, [mgr]);

  async function onEnable() {
    setBusy("enable");
    setError(null);
    try {
      await mgr.syncSubscription();
      if (typeof Notification !== "undefined") {
        setPermission(Notification.permission);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enable failed");
    } finally {
      setBusy(null);
    }
  }

  async function onDisable() {
    setBusy("disable");
    setError(null);
    try {
      await mgr.unsubscribe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Disable failed");
    } finally {
      setBusy(null);
    }
  }

  async function toggle(
    category: string,
    key: keyof CategoryPreference,
    value: boolean,
  ) {
    if (!prefs) return;
    setBusy(`${category}:${key}`);
    try {
      const updated = await mgr.setPreferences({
        [category]: { [key]: value },
      });
      setPrefs(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(null);
    }
  }

  async function onTest() {
    setBusy("test");
    setTestResult(null);
    setError(null);
    try {
      const { delivered } = await mgr.sendTest();
      setTestResult(
        delivered > 0
          ? `Delivered to ${delivered} device(s)`
          : "No active subscription -- enable notifications first",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Test failed");
    } finally {
      setBusy(null);
    }
  }

  if (!supported) {
    return (
      <p className="text-sm opacity-70">
        Your browser does not support Web Push notifications.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        {permission === "granted" ? (
          <>
            <Bell className="icon text-dsi-selected" />
            <span className="text-sm text-dsi-selected">
              Push notifications enabled
            </span>
            <button
              onClick={onDisable}
              disabled={busy === "disable"}
              className="ml-auto border-2 border-dsi-outline py-1 px-3 rounded text-sm"
            >
              Disable
            </button>
          </>
        ) : (
          <>
            <BellOff className="icon opacity-70" />
            <span className="text-sm opacity-80">
              Push notifications are {permission === "denied" ? "blocked" : "off"}.
            </span>
            <button
              onClick={onEnable}
              disabled={busy === "enable" || permission === "denied"}
              className="ml-auto bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
            >
              {busy === "enable" && <Loader2 className="icon animate-spin" />}
              Enable
            </button>
          </>
        )}
      </div>

      {permission === "granted" && (
        <div className="flex items-center gap-2">
          <button
            onClick={onTest}
            disabled={busy === "test"}
            className="border-2 border-dsi-outline py-1 px-3 rounded text-sm flex items-center gap-2"
          >
            {busy === "test" ? (
              <Loader2 className="icon animate-spin" />
            ) : (
              <Send className="icon" />
            )}
            Send test notification
          </button>
          {testResult && <span className="text-xs opacity-80">{testResult}</span>}
        </div>
      )}

      {prefs && (
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="text-xs uppercase opacity-60">
              <th className="text-left py-1">Category</th>
              <th className="w-20 text-center">In-app</th>
              <th className="w-20 text-center">Push</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(prefs).map(([cat, p]) => (
              <tr key={cat} className="border-t border-dsi-outline/20">
                <td className="py-2 pr-2">{CATEGORY_LABELS[cat] ?? cat}</td>
                <td className="text-center">
                  <input
                    type="checkbox"
                    checked={p.in_app}
                    disabled={busy === `${cat}:in_app`}
                    onChange={(e) => toggle(cat, "in_app", e.target.checked)}
                  />
                </td>
                <td className="text-center">
                  <input
                    type="checkbox"
                    checked={p.push}
                    disabled={busy === `${cat}:push`}
                    onChange={(e) => toggle(cat, "push", e.target.checked)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {error && <div className="text-sm text-dsi-negative">{error}</div>}
    </div>
  );
}
