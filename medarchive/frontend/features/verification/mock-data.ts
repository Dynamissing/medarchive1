export type VerificationPriority = "high" | "medium" | "low";
export type VerificationStatus = "open" | "in_review" | "blocked";

export type CandidateService = {
  id: string;
  name: string;
  code: string;
  confidence: number;
  reason: string;
};

export type VerificationItem = {
  id: string;
  document: string;
  partner: string;
  extractedName: string;
  sourceCode: string | null;
  amount: string;
  status: VerificationStatus;
  priority: VerificationPriority;
  anomalies: string[];
  snippet: string;
  extractedFields: Array<{ label: string; value: string }>;
  candidates: CandidateService[];
};

export const verificationQueueMock: VerificationItem[] = [
  {
    id: "verify-1024",
    document: "clinic-08-price-list.xlsx",
    partner: "Clinic 08",
    extractedName: "Complete blood count expanded",
    sourceCode: "LAB-001-A",
    amount: "3 200 KZT",
    status: "open",
    priority: "high",
    anomalies: ["price_change_gt_50_percent", "code_hint_mismatch"],
    snippet: "Row 48: Complete blood count expanded | LAB-001-A | resident 3200 | nonresident 3900",
    extractedFields: [
      { label: "Service name", value: "Complete blood count expanded" },
      { label: "Source code", value: "LAB-001-A" },
      { label: "Resident", value: "3 200 KZT" },
      { label: "Nonresident", value: "3 900 KZT" },
      { label: "Locator", value: "Sheet Prices, row 48" },
    ],
    candidates: [
      { id: "svc-001", name: "Complete blood count", code: "LAB-001", confidence: 91, reason: "name tokens and code prefix" },
      { id: "svc-004", name: "Complete blood count with differential", code: "LAB-004", confidence: 82, reason: "synonym overlap" },
      { id: "svc-019", name: "Blood chemistry panel", code: "LAB-019", confidence: 61, reason: "category overlap" },
    ],
  },
  {
    id: "verify-1023",
    document: "clinic-07-contract.docx",
    partner: "Clinic 07",
    extractedName: "Therapist initial visit",
    sourceCode: null,
    amount: "10 000 KZT",
    status: "in_review",
    priority: "medium",
    anomalies: ["missing_source_code"],
    snippet: "Table 2 row 12: Therapist initial visit - initial consultation - 10000",
    extractedFields: [
      { label: "Service name", value: "Therapist initial visit" },
      { label: "Source code", value: "Not detected" },
      { label: "Amount", value: "10 000 KZT" },
      { label: "Locator", value: "Table 2, row 12" },
    ],
    candidates: [
      { id: "svc-100", name: "General practitioner consultation", code: "CONS-100", confidence: 87, reason: "synonym and specialty" },
      { id: "svc-101", name: "Specialist initial consultation", code: "CONS-101", confidence: 74, reason: "token overlap" },
    ],
  },
  {
    id: "verify-1022",
    document: "legacy-scan-pack.pdf",
    partner: "Unknown",
    extractedName: "Chest imaging 1 projection",
    sourceCode: "IMG-010",
    amount: "8 500 KZT",
    status: "blocked",
    priority: "high",
    anomalies: ["low_ocr_confidence", "nonresident_lt_resident"],
    snippet: "OCR page 3: Chest imaging 1 projection ... IMG-010 ... 8500 ... confidence 62",
    extractedFields: [
      { label: "Service name", value: "Chest imaging 1 projection" },
      { label: "Source code", value: "IMG-010" },
      { label: "Amount", value: "8 500 KZT" },
      { label: "OCR confidence", value: "62%" },
      { label: "Locator", value: "Page 3" },
    ],
    candidates: [
      { id: "svc-010", name: "Chest X-ray", code: "IMG-010", confidence: 79, reason: "code hint" },
      { id: "svc-011", name: "Chest X-ray two projections", code: "IMG-011", confidence: 69, reason: "name tokens" },
    ],
  },
];
