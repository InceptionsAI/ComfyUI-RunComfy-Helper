import { app } from "../../../scripts/app.js";

// ComfyUI-Manager's legacy windows (Git Manager 3.39+, pip comfyui-manager up
// to 4.3) are built from PrimeVue dialog class names. Frontend 1.57 stopped
// loading PrimeVue's dialog styles, so these windows have no background.
// These rules repeat PrimeVue's own dialog rules for just these four windows.
// Where PrimeVue's variables are defined (frontends before 1.57) they resolve
// to the same values; otherwise the fallbacks, which are PrimeVue's defaults,
// apply. Manager versions with their own styles (ComfyUI-Manager #3392) no
// longer use the .p-dialog class, so the rules don't match them.
const windows = ".p-dialog:is(#cm-manager-dialog, #cn-manager-dialog, #cmm-manager-dialog, #snapshot-manager-dialog)";

const css = `
:where(${windows}) {
  border: 1px solid var(--p-dialog-border-color, var(--border-color));
  border-radius: var(--p-dialog-border-radius, 12px);
  background: var(--p-dialog-background, var(--comfy-menu-bg));
}

:where(${windows} > .p-dialog-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--p-dialog-header-padding, 1.25rem);
}

:where(${windows} > .p-dialog-content) {
  padding: var(--p-dialog-content-padding, 0 1.25rem 1.25rem 1.25rem);
}
`;

app.registerExtension({
  name: "runcomfy.ManagerDialogStyles",
  setup() {
    const style = document.createElement("style");
    style.id = "runcomfy-manager-dialog-styles";
    style.textContent = css;
    document.head.prepend(style);
  }
});
