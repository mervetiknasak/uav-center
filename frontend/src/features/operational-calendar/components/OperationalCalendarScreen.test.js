import { describe, expect, it } from "vitest";

import screenSource from "./OperationalCalendarScreen.vue?raw";
import tableSource from "./OperationalAlertsTable.vue?raw";

describe("operational calendar screen states", () => {
  it("exposes Turkish loading, error and empty states", () => {
    expect(screenSource).toContain(':show="loading"');
    expect(screenSource).toContain("Operasyonel uyarılar yükleniyor…");
    expect(screenSource).toContain("Operasyonel uyarılar alınamadı");
    expect(screenSource).toContain("Şu anda takip edilmesi gereken operasyonel uyarı bulunmuyor.");
    expect(tableSource).toContain(':description="emptyDescription"');
  });

  it("labels every interactive filter and keeps notification conditional", () => {
    expect(screenSource.match(/aria-label=/g)).toHaveLength(5);
    expect(tableSource).toContain("if (alert.can_notify)");
    expect(tableSource).toContain("Bildirim hazırla");
  });
});
