export type DocumentStatus = "pending" | "processing" | "parsed" | "failed";
export type DocumentFormat = "xlsx" | "xls" | "docx" | "pdf_text" | "pdf_ocr_candidate";

export type PriceDocumentRow = {
  id: string;
  file: string;
  partner: string | null;
  date: string | null;
  format: DocumentFormat;
  status: DocumentStatus;
  parsed_at: string | null;
};

export const documentsMock: PriceDocumentRow[] = [
  {
    id: "doc-1008",
    file: "clinic-08-price-list.xlsx",
    partner: "Clinic 08",
    date: "2026-06-24",
    format: "xlsx",
    status: "parsed",
    parsed_at: "2026-06-27 09:34",
  },
  {
    id: "doc-1007",
    file: "clinic-07-contract.docx",
    partner: "Clinic 07",
    date: "2026-06-22",
    format: "docx",
    status: "processing",
    parsed_at: null,
  },
  {
    id: "doc-1006",
    file: "clinic-05-public-prices.pdf",
    partner: "Clinic 05",
    date: "2026-06-21",
    format: "pdf_text",
    status: "parsed",
    parsed_at: "2026-06-27 08:51",
  },
  {
    id: "doc-1005",
    file: "legacy-scan-pack.pdf",
    partner: null,
    date: null,
    format: "pdf_ocr_candidate",
    status: "failed",
    parsed_at: null,
  },
  {
    id: "doc-1004",
    file: "clinic-04-tariffs.xls",
    partner: "Clinic 04",
    date: "2026-06-18",
    format: "xls",
    status: "pending",
    parsed_at: null,
  },
  {
    id: "doc-1003",
    file: "clinic-01-services.pdf",
    partner: "Clinic 01",
    date: "2026-06-16",
    format: "pdf_text",
    status: "parsed",
    parsed_at: "2026-06-27 07:42",
  },
];
