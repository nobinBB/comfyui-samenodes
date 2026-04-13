import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Register extension for SeedStepN node
app.registerExtension({
    name: "comfyui.samenodes.SeedStepN",

    async nodeCreated(node) {
        if (node.comfyClass !== "SeedStepN") {
            return;
        }

        // Add custom display widgets
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

        const nextSeedWidget = node.addCustomWidget({
            name: "next_seed_display",
            type: "custom_text",
            value: "Next seed: 0",
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
            fetch("/samenodes/reset_seed_counter", {
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
                    updateNextSeed();
                    node.setDirtyCanvas(true);
                } else {
                    console.error("Failed to reset counter");
                }
            })
            .catch(error => {
                console.error("Error resetting counter:", error);
            });
        });

        // Function to update next seed display
        const updateNextSeed = () => {
            const baseSeedWidget = node.widgets.find(w => w.name === "base_seed");
            const divisorWidget = node.widgets.find(w => w.name === "divisor");
            const incrementWidget = node.widgets.find(w => w.name === "increment_amount");

            if (baseSeedWidget && divisorWidget && incrementWidget) {
                const baseSeed = baseSeedWidget.value || 0;
                const divisor = divisorWidget.value || 1;
                const increment = incrementWidget.value || 1;

                // Parse current count from display
                const countMatch = countWidget.value.match(/Count: (\d+)/);
                const currentCount = countMatch ? parseInt(countMatch[1]) : 0;

                // Calculate next seed
                const nextCount = currentCount + 1;
                const nextSeed = baseSeed + Math.floor(nextCount / divisor) * increment;

                nextSeedWidget.value = `Next seed: ${nextSeed}`;
            }
        };

        // Update next seed display when parameters change
        const baseSeedWidget = node.widgets.find(w => w.name === "base_seed");
        const divisorWidget = node.widgets.find(w => w.name === "divisor");
        const incrementWidget = node.widgets.find(w => w.name === "increment_amount");

        if (baseSeedWidget) {
            const originalCallback = baseSeedWidget.callback;
            baseSeedWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateNextSeed();
            };
        }

        if (divisorWidget) {
            const originalCallback = divisorWidget.callback;
            divisorWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateNextSeed();
            };
        }

        if (incrementWidget) {
            const originalCallback = incrementWidget.callback;
            incrementWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                updateNextSeed();
            };
        }

        // Listen for execution complete events
        api.addEventListener("executed", (event) => {
            const data = event.detail;

            if (data.node === node.id.toString()) {
                // Node was executed, update display from backend data
                if (data.output && data.output.count && data.output.count.length > 0) {
                    const newCount = data.output.count[0];
                    const nextSeed = data.output.next_seed && data.output.next_seed.length > 0
                        ? data.output.next_seed[0]
                        : 0;

                    countWidget.value = `Count: ${newCount}`;
                    nextSeedWidget.value = `Next seed: ${nextSeed}`;
                    node.setDirtyCanvas(true);

                    console.log(`SeedStepN (${node.id}): Count updated to ${newCount}, Next seed: ${nextSeed}`);
                }
            }
        });

        // Initial update
        updateNextSeed();
    }
});
