import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.lootwallet.app",
  appName: "Loot Wallet",
  webDir: "out",
  ios: {
    contentInset: "automatic",
  },
};
export default config;
