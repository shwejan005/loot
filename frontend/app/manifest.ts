import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Loot Wallet",
    short_name: "Loot",
    description: "Money, made smarter.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#721e3b",
    categories: ["finance"],
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  };
}
