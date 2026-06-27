import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/styles/globals.css";
import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  title: "MedArchive / MedPartners",
  description: "Clinical-tech UI foundation for archive intake and partner price review.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
