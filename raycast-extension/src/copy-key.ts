import { Clipboard, showHUD, showToast, Toast } from "@raycast/api";
import { masterKey, prefs } from "./lib";

export default async function CopyKeyCommand() {
  const p = prefs();
  const key = masterKey(p);

  if (!key) {
    await showToast({
      style: Toast.Style.Failure,
      title: "No key found",
      message: "Set MODELROUTER_MASTER_KEY in extension preferences, or check your .env",
    });
    return;
  }

  await Clipboard.copy(key);
  await showHUD("Master key copied to clipboard");
}
