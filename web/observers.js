import { app } from "../../../scripts/app.js";

app.registerExtension({
  name: "runcomfy.Observers",
  async setup() {
    document.addEventListener('click', function (event) {
      if (event.target.matches('button.cm-button-red') ||
        event.target.matches('button.cn-manager-restart')) {
        window.parent.postMessage({ type: "notification", event: "runcomfy.workflow_env_changed" }, "*");
      }
    });
  }
});
