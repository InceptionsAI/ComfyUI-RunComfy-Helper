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
app.registerExtension({
	name: "runcomfy.Workflows",
	async setup() {
        const customWorkflow = await getWorkflow();
        if (customWorkflow === null) {
            console.log("Workflow not found");
            return;
        }
        await app.loadGraphData(customWorkflow);

        console.log("Custom workflow loaded by runcomfy.Workflows extension");
	}
});
