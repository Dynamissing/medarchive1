export type PartnerPriceStatus = "current" | "outdated" | "missing" | "unmatched";

export type PartnerPrice = {
  id: string;
  partner: string;
  residentPrice: number | null;
  nonresidentPrice: number | null;
  currency: "KZT" | "USD";
  effectiveDate: string | null;
  status: PartnerPriceStatus;
  note: string | null;
};

export type ServiceDetail = {
  id: string;
  title: string;
  code: string;
  category: string;
  specialty: string;
  description: string;
  partners: PartnerPrice[];
};

export const serviceDetailMock: ServiceDetail = {
  id: "svc-001",
  title: "Complete blood count",
  code: "LAB-001",
  category: "Laboratory",
  specialty: "Diagnostics",
  description: "Common blood test service normalized across imported partner price documents.",
  partners: [
    {
      id: "partner-08",
      partner: "Clinic 08",
      residentPrice: 2500,
      nonresidentPrice: 3000,
      currency: "KZT",
      effectiveDate: "2026-06-01",
      status: "current",
      note: null,
    },
    {
      id: "partner-07",
      partner: "Clinic 07",
      residentPrice: 2700,
      nonresidentPrice: 3400,
      currency: "KZT",
      effectiveDate: "2026-05-12",
      status: "current",
      note: null,
    },
    {
      id: "partner-05",
      partner: "Clinic 05",
      residentPrice: 2200,
      nonresidentPrice: null,
      currency: "KZT",
      effectiveDate: "2026-02-18",
      status: "missing",
      note: "Nonresident price not detected",
    },
    {
      id: "partner-legacy",
      partner: "Legacy scan batch",
      residentPrice: null,
      nonresidentPrice: null,
      currency: "KZT",
      effectiveDate: null,
      status: "unmatched",
      note: "Extracted row awaits manual match",
    },
    {
      id: "partner-02",
      partner: "Clinic 02",
      residentPrice: 1900,
      nonresidentPrice: 2500,
      currency: "KZT",
      effectiveDate: "2025-09-30",
      status: "outdated",
      note: "Older accepted version",
    },
  ],
};
