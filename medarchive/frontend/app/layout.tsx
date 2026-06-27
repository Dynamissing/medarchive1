import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/styles/globals.css";
import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: {
    default: "MedPrice - сравнение цен на медицинские услуги в Казахстане",
    template: "%s",
  },
  description:
    "Сравнивайте цены на анализы, диагностику и приемы врачей в клиниках Казахстана. Поиск по услугам, городам, клиникам и источникам данных.",
  applicationName: "MedPrice",
  creator: "MedPrice",
  publisher: "MedPrice",
  robots: { index: true, follow: true },
  openGraph: {
    title: "MedPrice - сравнение цен на медицинские услуги в Казахстане",
    description:
      "Сравнивайте цены на анализы, диагностику и приемы врачей в клиниках Казахстана. Поиск по услугам, городам, клиникам и источникам данных.",
    url: "/",
    siteName: "MedPrice",
    type: "website",
    locale: "ru_KZ",
    images: [{ url: "/og/medprice.svg", width: 1200, height: 630, alt: "MedPrice" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "MedPrice - сравнение цен на медицинские услуги в Казахстане",
    description:
      "Сравнивайте цены на анализы, диагностику и приемы врачей в клиниках Казахстана. Поиск по услугам, городам, клиникам и источникам данных.",
    images: ["/og/medprice.svg"],
  },
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
