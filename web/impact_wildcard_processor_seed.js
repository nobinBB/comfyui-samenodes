import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Register extension for ImpactWildcardProcessorSeed node
app.registerExtension({
    name: "comfyui.samenodes.ImpactWildcardProcessorSeed",

    async nodeCreated(node) {
        if (node.comfyClass !== "ImpactWildcardProcessorSeed") {
            return;
        }

        // Add custom display widgets
        const seedWidget = node.addCustomWidget({
            name: "seed_display",
            type: "custom_text",
            value: "Seed: 0",
            options: {},
            draw: function(ctx, node, widgetWidth, y, widgetHeight) {
                const margin = 10;
                ctx.save();
                ctx.fillStyle = "#AAA";
                ctx.font = "12px Arial";
                ctx.fillText(this.value, margin, y + widgetHeight * 0.7);
                ctx.restore();
                return y + widgetHeight;
            },
            computeSize: function(width) {
                return [width, 20];
            }
        });

        const countWidget = node.addCustomWidget({
            name: "count_display",
            type: "custom_text",
            value: "Count: 0",
            options: {},
            draw: function(ctx, node, widgetWidth, y, widgetHeight) {
                const margin = 10;
                ctx.save();
                ctx.fillStyle = "#AAA";
                ctx.font = "12px Arial";
                ctx.fillText(this.value, margin, y + widgetHeight * 0.7);
                ctx.restore();
                return y + widgetHeight;
            },
            computeSize: function(width) {
                return [width, 20];
            }
        });

        // Add reset button
        const resetButton = node.addWidget("button", "Reset Counter", null, () => {
            const nodeId = node.id;

            // Call backend API to reset counter
            fetch("/samenodes/reset_wildcard_seed_counter", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    unique_id: nodeId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Counter reset for node ${nodeId}`);
                    // Update display
                    countWidget.value = "Count: 0";
                    updateSeedDisplay();
                    node.setDirtyCanvas(true);
                } else {
                    console.error("Failed to reset counter");
                }
            })
            .catch(error => {
                console.error("Error resetting counter:", error);
            });
        });

        // Function to update seed display based on current parameters
        const updateSeedDisplay = () => {
            const seedModeWidget = node.widgets.find(w => w.name === "seed_mode");
            const seedWidget_input = node.widgets.find(w => w.name === "seed");

            if (seedModeWidget && seedWidget_input) {
                const seedMode = seedModeWidget.value || "random";
                const seed = seedWidget_input.value || 0;

                // Parse current count from display
                const countMatch = countWidget.value.match(/Count: (\d+)/);
                const currentCount = countMatch ? parseInt(countMatch[1]) : 0;

                // Show seed mode info
                let seedInfo = `Seed mode: ${seedMode}`;
                if (seedMode !== "random") {
                    seedInfo += ` (seed: ${seed})`;
                }
                seedWidget.value = seedInfo;
            }
        };

        // Update seed display when parameters change
        const seedModeWidget = node.widgets.find(w => w.name === "seed_mode");
        const seedWidget_input = node.widgets.find(w => w.name === "seed");
        const divisorWidget = node.widgets.find(w => w.name === "divisor");
        const incrementWidget = node.widgets.find(w => w.name === "increment_amount");

        if (seedModeWidget) {
            const originalCallback = seedModeWidget.callback;
            seedModeWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateSeedDisplay();
            };
        }

        if (seedWidget_input) {
            const originalCallback = seedWidget_input.callback;
            seedWidget_input.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateSeedDisplay();
            };
        }

        if (divisorWidget) {
            const originalCallback = divisorWidget.callback;
            divisorWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateSeedDisplay();
            };
        }

        if (incrementWidget) {
            const originalCallback = incrementWidget.callback;
            incrementWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateSeedDisplay();
            };
        }

        // Listen for execution complete events
        api.addEventListener("executed", (event) => {
            const data = event.detail;

            if (data.node === node.id.toString()) {
                // Node was executed, update display from backend data
                if (data.output) {
                    if (data.output.seed && data.output.seed.length > 0) {
                        const seed = data.output.seed[0];
                        const seedModeWidget = node.widgets.find(w => w.name === "seed_mode");
                        const seedMode = seedModeWidget ? seedModeWidget.value : "random";
                        seedWidget.value = `Seed: ${seed} (${seedMode})`;
                    }

                    if (data.output.count && data.output.count.length > 0) {
                        const count = data.output.count[0];
                        countWidget.value = `Count: ${count}`;
                    }

                    node.setDirtyCanvas(true);

                    console.log(`ImpactWildcardProcessorSeed (${node.id}): Updated display`);
                }
            }
        });

        // Initial update
        updateSeedDisplay();
    }
});
