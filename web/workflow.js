import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function getWorkflow(name) {
	try {
		const response = await api.fetchApi(`/runcomfy/workflows?name=${name}`, { cache: "no-store" });
		if (response.status != 200) {
			return null;
		}
		return await response.json();
	} catch (error) {
		// Handle other errors
		console.error(error);
		return null;
	}
}

function hasPreloadedWorkflow() {
	var loaded = localStorage.getItem('runcomfy.has_preloaded_workflow');
	if (loaded) {
		return true
	} else {
		localStorage.setItem('runcomfy.has_preloaded_workflow', true);
		return false
	}
}

app.registerExtension({
	name: "runcomfy.Workflows",
	async setup() {
		window.addEventListener('message', async (event) => {

			// Determine the target origin
			const targetOrigin = event.origin !== "null" && event.origin !== "" ? event.origin : "*";
			// if the event data is runcomfy.get_current_workflow, then send the graph data back to the parent
			if (event.data == "runcomfy.get_current_workflow") {
				const json = app.graph.serialize();
				// Send response back to parent
				// wrap this json into a json object {event: "runcomfy.get_current_workflow", data: json}
				event.source.postMessage({ type: "workflow", event: "runcomfy.get_current_workflow", data: json }, targetOrigin);
			}
		});
		if (!hasPreloadedWorkflow()) {
			const customWorkflow = await getWorkflow();
			if (customWorkflow === null) {
				return;
			}
			await app.loadGraphData(customWorkflow);

			console.log("Custom workflow loaded by runcomfy.Workflows extension");
		}
	}

});
