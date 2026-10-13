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
		return false
	}
}

app.registerExtension({
	name: "runcomfy.Workflows",
	async init() {
		window.addEventListener('message', async (event) => {
			// Determine the target origin
			const targetOrigin = event.origin !== "null" && event.origin !== "" ? event.origin : "*";
			// if the event data is runcomfy.get_current_workflow, then send the graph data back to the parent
			if (event.data == "runcomfy.get_current_workflow") {
				const json = app.graph.serialize();
				console.log("helper got workflow", json)
				// Send response back to parent
				// wrap this json into a json object {event: "runcomfy.get_current_workflow", data: json}
				event.source.postMessage({ type: "workflow", event: "runcomfy.get_current_workflow", data: json }, targetOrigin);
			}
		});

		if (!hasPreloadedWorkflow()) {
			const customWorkflow = await getWorkflow();
			if (!Array.isArray(customWorkflow?.nodes)) {
				return;
			}
			// New users get a blank canvas and the templates browser instead of the default graph; skip that.
			// The setting only exists on frontend 1.8.7+.
			if (app.extensionManager?.setting?.get('Comfy.TutorialCompleted') === false) {
				await app.extensionManager.setting.set('Comfy.TutorialCompleted', true);
			}
			// The first startup load either restores the user's own workflow or, with nothing to restore,
			// loads the default graph via loadGraphData() without data. Load the RunComfy workflow for the latter.
			const loadGraphData = app.loadGraphData;
			let pending = true;
			app.loadGraphData = function (graphData, ...args) {
				if (pending) {
					pending = false;
					localStorage.setItem('runcomfy.has_preloaded_workflow', true);
					if (!graphData) {
						console.log("Loading custom workflow by runcomfy.Workflows extension");
						// Go through app.loadGraphData again so wrappers added after this one see the workflow too.
						return app.loadGraphData(customWorkflow, ...args);
					}
				}
				return loadGraphData.apply(this, arguments);
			};
		}
	}

});
