import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/styles/globals.css";
import { Providers } from "@/app/providers";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata();

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru" className="dark">
      <body>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(()=>{var p=location.pathname.split('/').filter(Boolean)[0];var l=p==='kz'?'kk-KZ':p==='en'?'en':'ru';document.documentElement.lang=l;})();",
          }}
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
