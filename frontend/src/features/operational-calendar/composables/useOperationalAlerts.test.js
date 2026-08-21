import { describe, expect, it, vi } from "vitest";

import { useOperationalAlerts } from "./useOperationalAlerts";

describe("operational alert transport", () => {
  it("loads and normalizes the read-only alert response", async () => {
    const apiFetch = vi.fn().mockResolvedValue({
      as_of: "2026-08-20",
      thresholds: { critical_days: 7, horizon_days: 30, stale_days: 14 },
      summary: { total: 1, overdue: 1, next_7_days: 0, next_30_days: 0, stale: 0 },
      alerts: [{ key: "flight_permit:3:valid_until" }]
    });
    const operationalAlerts = useOperationalAlerts(apiFetch);

    await operationalAlerts.loadAlerts();

    expect(apiFetch).toHaveBeenCalledWith("/api/operational-alerts/");
    expect(operationalAlerts.data.value.summary.total).toBe(1);
    expect(operationalAlerts.data.value.alerts).toHaveLength(1);
    expect(operationalAlerts.loading.value).toBe(false);
  });

  it("keeps a Turkish user-facing error when loading fails", async () => {
    const operationalAlerts = useOperationalAlerts(vi.fn().mockRejectedValue(new Error("offline")));

    await operationalAlerts.loadAlerts();

    expect(operationalAlerts.error.value).toContain("offline");
    expect(operationalAlerts.loading.value).toBe(false);
  });
});
