import { app } from "../../../scripts/app.js";

// The RunComfy machine page asks ComfyUI to open ComfyUI-Manager with a
// "runcomfy.open_manager" message and gets back
// { type: "manager", event: "runcomfy.open_manager", opened }, so it can tell
// the user when this machine has no Manager to open.

// Registered by the Manager's own menu (Git Manager, and pip comfyui-manager
// with the legacy UI) on frontends that have commands. It is what the
// Manager button, and on frontend 1.57+ the Extensions button, runs.
const MANAGER_MENU_COMMAND = "Comfy.Manager.Menu.ToggleVisibility";

async function openManager() {
	const command = app.extensionManager?.command;
	if (command?.execute) {
		try {
			await command.execute(MANAGER_MENU_COMMAND);
			return true;
		} catch (error) {
			// Not registered: no Manager, or one that predates commands.
		}
	}
	// Frontends and Managers without commands put a "Manager" button in the menu.
	const button = Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Manager");
	if (button) {
		button.click();
		return true;
	}
	return false;
}

app.registerExtension({
	name: "runcomfy.OpenManager",
	// setup runs once ComfyUI has loaded and every extension has registered its
	// commands and buttons. Before that there is no reply, so the page can tell
	// "still loading" apart from "no Manager".
	async setup() {
		window.addEventListener("message", async (event) => {
			if (event.data !== "runcomfy.open_manager") {
				return;
			}
			const targetOrigin = event.origin !== "null" && event.origin !== "" ? event.origin : "*";
			const opened = await openManager();
			event.source?.postMessage({ type: "manager", event: "runcomfy.open_manager", opened }, targetOrigin);
		});
	},
});
