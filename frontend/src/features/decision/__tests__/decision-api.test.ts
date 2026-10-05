import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzePricingQuery } from "@/features/decision/decision-api";

describe("analyzePricingQuery presentation boundary", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fails closed when the backend returns an unknown presentation status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "FUTURE_READY",
          headline: "RAZONABLE",
          summary: "El precio es razonable.",
        }),
      }),
    );

    const result = await analyzePricingQuery("soporte técnico por $35.000");

    expect(result).toEqual({
      kind: "abstention",
      conclusion: "No puedo interpretar este resultado con seguridad.",
    });
  });
});
