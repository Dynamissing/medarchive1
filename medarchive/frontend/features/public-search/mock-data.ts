export type PublicSearchResult = {
  id: string;
  type: "service" | "partner";
  title: string;
  subtitle: string;
  category: string;
  priceRange: string;
  partnerCount: number;
};

export const quickExamples = ["blood test", "x-ray", "consultation", "MRI", "home nurse"];

export const topCategories = ["Diagnostics", "Radiology", "Consultation", "Laboratory", "Home care"];

export const publicSearchResultsMock: PublicSearchResult[] = [
  {
    id: "svc-001",
    type: "service",
    title: "Complete blood count",
    subtitle: "LAB-001 - common laboratory diagnostic service",
    category: "Laboratory",
    priceRange: "2 500-3 900 KZT",
    partnerCount: 18,
  },
  {
    id: "svc-010",
    type: "service",
    title: "Chest X-ray",
    subtitle: "IMG-010 - single projection chest imaging",
    category: "Radiology",
    priceRange: "7 000-8 500 KZT",
    partnerCount: 11,
  },
  {
    id: "partner-07",
    type: "partner",
    title: "Clinic 07",
    subtitle: "Active partner with reviewed service prices",
    category: "Partner",
    priceRange: "124 active prices",
    partnerCount: 1,
  },
  {
    id: "svc-100",
    type: "service",
    title: "General practitioner consultation",
    subtitle: "CONS-100 - primary care consultation",
    category: "Consultation",
    priceRange: "10 000-12 000 KZT",
    partnerCount: 23,
  },
];
