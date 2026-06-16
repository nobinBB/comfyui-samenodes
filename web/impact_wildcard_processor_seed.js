import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Minimal frontend for ImpactWildcardProcessorSeed.
// Shows only populate execution count.

app.registerExtension({
    name: "comfyui.samenodes.ImpactWildcardProcessorSeed",

    async nodeCreated(node) {
        if (node.comfyClass !== "ImpactWildcardProcessorSeed") {
            return;
        }

        const countWidget = node.addCustomWidget({
            name: "count_display",
            type: "custom_text",
            value: "Populate runs: 0",
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

        const resetButton = node.addWidget("button", "Reset Count / Cache", null, () => {
            const nodeId = node.id;

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
                    countWidget.value = "Populate runs: 0";
                    node.setDirtyCanvas(true);
                    console.log(`ImpactWildcardProcessorSeed: counter/cache reset for node ${nodeId}`);
                } else {
                    console.error("ImpactWildcardProcessorSeed: failed to reset counter/cache", data.error);
                }
            })
            .catch(error => {
                console.error("ImpactWildcardProcessorSeed: error resetting counter/cache:", error);
            });
        });

        const modeWidget = node.widgets.find(w => w.name === "mode");
        const populatedTextWidget = node.widgets.find(w => w.name === "populated_text");
        const wildcardTextWidget = node.widgets.find(w => w.name === "wildcard_text");
        const selectWildcardWidget = node.widgets.find(w => w.name === "Select to add Wildcard");

        if (selectWildcardWidget && wildcardTextWidget) {
            const originalCallback = selectWildcardWidget.callback;

            selectWildcardWidget.callback = function(value) {
                if (originalCallback) {
                    originalCallback.call(this, value);
                }

                if (value && value !== "Select the Wildcard to add to the text") {
                    const currentText = wildcardTextWidget.value || "";
                    const separator = currentText.length > 0 ? ", " : "";
                    wildcardTextWidget.value = currentText + separator + value;

                    selectWildcardWidget.value = "Select the Wildcard to add to the text";

                    node.setDirtyCanvas(true);
                }
            };
        }

        const updateWidgetStates = () => {
            if (!modeWidget || !populatedTextWidget || !populatedTextWidget.inputEl) {
                return;
            }

            if (modeWidget.value === "populate") {
                populatedTextWidget.inputEl.disabled = true;
                populatedTextWidget.inputEl.placeholder = "Populated Prompt (generated automatically)";
            } else {
                populatedTextWidget.inputEl.disabled = false;
                populatedTextWidget.inputEl.placeholder = "Populated Prompt (fixed/reproduce output)";
            }
        };

        if (modeWidget) {
            const originalCallback = modeWidget.callback;

            modeWidget.callback = function(value) {
                if (originalCallback) {
                    originalCallback.call(this, value);
                }

                updateWidgetStates();
            };
        }

        api.addEventListener("executed", (event) => {
            const data = event.detail;

            if (data.node !== node.id.toString()) {
                return;
            }

            if (!data.output) {
                return;
            }

            if (data.output.count && data.output.count.length > 0) {
                const count = data.output.count[0];
                countWidget.value = `Populate runs: ${count}`;
            }

            if (data.output.populated_text && data.output.populated_text.length > 0 && populatedTextWidget) {
                populatedTextWidget.value = data.output.populated_text[0];
            }

            if (modeWidget && modeWidget.value === "reproduce") {
                modeWidget.value = "populate";
                updateWidgetStates();
            }

            node.setDirtyCanvas(true);
        });

        updateWidgetStates();
    }
});