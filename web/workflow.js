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

// Apply rgthree workaround to prevent empty workflow override
function applyRgthreeWorkaround() {
	let isSuccessfullyLoaded = false;
	let lastSuccessfulLoadTime = 0;

	// backup original function
	const originalLoadGraphData = app.loadGraphData;
	app.loadGraphData = function (graph) {
		const incomingNodeCount = graph?.nodes?.length || 0;
		const currentNodeCount = app.graph?.nodes?.length || 0;
		const now = Date.now();

		// Check if current workflow has rgthree nodes
		const isRgthreeLoading = app.graph?.nodes?.some(node =>
			node.type && node.type.includes('(rgthree)')
		) || false;

		if (isRgthreeLoading) {
			console.log("[RunComfy] Rgthree is loading");
		}
		// status check: Prevent rgthree's empty workflow "fix" from overriding loaded workflows
		const isRgthreeAutoFix = now - lastSuccessfulLoadTime < 1500;
		const isRgthreeOverride = incomingNodeCount === 0 &&
			currentNodeCount > 0 &&
			isSuccessfullyLoaded &&
			isRgthreeAutoFix &&
			isRgthreeLoading;

		if (isRgthreeOverride) {
			console.log("[RunComfy] Prevented empty workflow override caused by rgthree link-fixer");
			return Promise.resolve();
		}

		// Track successful loads
		if (incomingNodeCount > 0) {
			isSuccessfullyLoaded = true;
			lastSuccessfulLoadTime = now;
		}

		return originalLoadGraphData.apply(this, arguments);
	};
}



app.registerExtension({
	name: "runcomfy.Workflows",
	async setup() {
		// Apply rgthree workaround (only activates when rgthree nodes are present)
		applyRgthreeWorkaround();

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
			if (customWorkflow === null) {
				return;
			}
			await app.loadGraphData(customWorkflow);
			localStorage.setItem('runcomfy.has_preloaded_workflow', true);
			console.log("Custom workflow loaded by runcomfy.Workflows extension");
		}
	}

}); 
