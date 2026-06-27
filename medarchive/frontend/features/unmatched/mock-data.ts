export type UnmatchedStatus = "new" | "reviewing" | "deferred";

export type UnmatchedItem = {
  id: string;
  document: string;
  partner: string;
  normalizedQuery: string;
  sourceCode: string | null;
  amount: string;
  status: UnmatchedStatus;
  reason: string;
};

export type DirectoryServiceResult = {
  id: string;
  name: string;
  code: string;
  specialty: string;
  confidence: number;
};

export const unmatchedItemsMock: UnmatchedItem[] = [
  {
    id: "unmatched-301",
    document: "clinic-08-price-list.xlsx",
    partner: "Clinic 08",
    normalizedQuery: "expanded blood count panel",
    sourceCode: "LAB-001-A",
    amount: "3 200 KZT",
    status: "new",
    reason: "No candidate passed review threshold",
  },
  {
    id: "unmatched-300",
    document: "legacy-scan-pack.pdf",
    partner: "Unknown",
    normalizedQuery: "xray thorax single view",
    sourceCode: "IMG-010",
    amount: "8 500 KZT",
    status: "reviewing",
    reason: "OCR text and source code disagree",
  },
  {
    id: "unmatched-299",
    document: "clinic-07-contract.docx",
    partner: "Clinic 07",
    normalizedQuery: "home nurse call adult",
    sourceCode: null,
    amount: "12 000 KZT",
    status: "deferred",
    reason: "Missing service code",
  },
];

export const directoryResultsMock: DirectoryServiceResult[] = [
  {
    id: "svc-001",
    name: "Complete blood count",
    code: "LAB-001",
    specialty: "Diagnostics",
    confidence: 83,
  },
  {
    id: "svc-004",
    name: "Complete blood count with differential",
    code: "LAB-004",
    specialty: "Diagnostics",
    confidence: 78,
  },
  {
    id: "svc-010",
    name: "Chest X-ray",
    code: "IMG-010",
    specialty: "Radiology",
    confidence: 74,
  },
  {
    id: "svc-111",
    name: "Home nurse visit",
    code: "NURS-111",
    specialty: "Home care",
    confidence: 69,
  },
  {
    id: "svc-100",
    name: "General practitioner consultation",
    code: "CONS-100",
    specialty: "Consultation",
    confidence: 52,
  },
];
