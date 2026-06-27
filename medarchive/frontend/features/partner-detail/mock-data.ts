export type PartnerPriceRow = {
  id: string;
  service: string;
  code: string;
  category: string;
  residentPrice: number | null;
  nonresidentPrice: number | null;
  currency: "KZT";
  effectiveDate: string;
  status: "current" | "review" | "missing";
};

export type PartnerDocumentHistory = {
  id: string;
  filename: string;
  importedAt: string;
  parsedRows: number;
  status: "parsed" | "review" | "failed";
};

export type PartnerDetail = {
  id: string;
  name: string;
  region: string;
  contact: {
    phone: string | null;
    email: string | null;
    address: string | null;
  };
  latestDocumentDate: string;
  prices: PartnerPriceRow[];
  history: PartnerDocumentHistory[];
};

export const partnerDetailMock: PartnerDetail = {
  id: "partner-07",
  name: "Clinic 07",
  region: "Almaty",
  contact: {
    phone: "+7 727 000 00 07",
    email: null,
    address: "12 Abay Ave",
  },
  latestDocumentDate: "2026-06-22",
  prices: [
    {
      id: "price-1",
      service: "Complete blood count",
      code: "LAB-001",
      category: "Laboratory",
      residentPrice: 2700,
      nonresidentPrice: 3400,
      currency: "KZT",
      effectiveDate: "2026-05-12",
      status: "current",
    },
    {
      id: "price-2",
      service: "Chest X-ray",
      code: "IMG-010",
      category: "Radiology",
      residentPrice: 7200,
      nonresidentPrice: 8500,
      currency: "KZT",
      effectiveDate: "2026-05-12",
      status: "current",
    },
    {
      id: "price-3",
      service: "General practitioner consultation",
      code: "CONS-100",
      category: "Consultation",
      residentPrice: 10000,
      nonresidentPrice: 12000,
      currency: "KZT",
      effectiveDate: "2026-05-12",
      status: "review",
    },
    {
      id: "price-4",
      service: "Home nurse visit",
      code: "NURS-111",
      category: "Home care",
      residentPrice: 12000,
      nonresidentPrice: null,
      currency: "KZT",
      effectiveDate: "2026-05-12",
      status: "missing",
    },
  ],
  history: [
    { id: "doc-7-3", filename: "clinic-07-contract.docx", importedAt: "2026-06-22", parsedRows: 124, status: "parsed" },
    { id: "doc-7-2", filename: "clinic-07-prices-may.xlsx", importedAt: "2026-05-12", parsedRows: 118, status: "review" },
    { id: "doc-7-1", filename: "clinic-07-legacy.pdf", importedAt: "2026-03-02", parsedRows: 91, status: "parsed" },
  ],
};
