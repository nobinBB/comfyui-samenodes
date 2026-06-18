import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

let wildcardsList = [];
let wildcardStatus = {
    onDemandMode: false,
    loadedCount: 0,
};

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function isSelectLabel(value) {
    const text = String(value ?? "");

    return (
        text === "" ||
        text === "Select the Wildcard to add to the text" ||
        text === "Select Wildcard Full Cache" ||
        text.startsWith("Select Wildcard On-Demand:")
    );
}

function wildcardLabel() {
    if (wildcardStatus.onDemandMode) {
        return `Select Wildcard On-Demand: ${wildcardStatus.loadedCount} loaded`;
    }

    return "Select Wildcard Full Cache";
}

async function loadWildcards() {
    try {
        const res = await api.fetchApi("/impact/wildcards/list");
        const json = await res.json();

        if (Array.isArray(json)) {
            wildcardsList = json;
        } else if (Array.isArray(json.data)) {
            wildcardsList = json.data;
        } else {
            wildcardsList = [];
        }
    } catch (e) {
        console.error("[ImpactWildcardProcessorTitle] loadWildcards failed:", e);
        wildcardsList = [];
    }
}

async function loadWildcardStatus() {
    try {
        const res = await api.fetchApi("/impact/wildcards/list/loaded");
        const json = await res.json();

        wildcardStatus = {
            onDemandMode: !!json.on_demand_mode,
            loadedCount: Array.isArray(json.data) ? json.data.length : 0,
        };
    } catch (e) {
        wildcardStatus = {
            onDemandMode: false,
            loadedCount: 0,
        };
    }
}

function setWidgetValue(node, widget, value) {
    if (!widget) return;

    widget.value = value;

    if (widget.inputEl) {
        widget.inputEl.value = value;
    }

    if (node.widgets_values) {
        const index = node.widgets.indexOf(widget);
        if (index >= 0) {
            node.widgets_values[index] = value;
        }
    }

    node.setDirtyCanvas(true, true);
}

function appendWildcard(node, wildcardValue) {
    if (isSelectLabel(wildcardValue)) return;

    const wildcardTextWidget = findWidget(node, "wildcard_text");
    if (!wildcardTextWidget) return;

    let current = String(wildcardTextWidget.value ?? "");

    if (current.trim() !== "") {
        current += ", ";
    }

    current += wildcardValue;

    setWidgetValue(node, wildcardTextWidget, current);
}

Promise.all([
    loadWildcards(),
    loadWildcardStatus(),
]);

api.addEventListener("samenodes-impact-wildcard-title-populated", (event) => {
    const detail = event.detail || {};
    const node = app.graph.getNodeById(Number(detail.node_id));

    if (!node) return;

    const populatedTextWidget = findWidget(node, "populated_text");
    setWidgetValue(node, populatedTextWidget, detail.value ?? "");
});

api.addEventListener("executed", async () => {
    if (wildcardStatus.onDemandMode) {
        await loadWildcardStatus();
        await loadWildcards();
        app.canvas.setDirty(true, true);
    }
});

app.registerExtension({
    name: "samenodes.ImpactWildcardProcessorTitle",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ImpactWildcardProcessorTitle") {
            return;
        }

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);

            const wildcardTextWidget = findWidget(this, "wildcard_text");
            const populatedTextWidget = findWidget(this, "populated_text");
            const modeWidget = findWidget(this, "mode");
            const wildcardSelectWidget = findWidget(this, "Select to add Wildcard");

            if (wildcardTextWidget?.inputEl) {
                wildcardTextWidget.inputEl.placeholder = "Wildcard Prompt (User input)";
            }

            if (populatedTextWidget?.inputEl) {
                populatedTextWidget.inputEl.placeholder = "Populated Prompt (Will be generated automatically)";
            }

            if (modeWidget) {
                if (modeWidget.value === "randomize") {
                    setWidgetValue(this, modeWidget, "populate");
                }

                const originalModeCallback = modeWidget.callback;

                modeWidget.callback = (value, canvas, node, pos, e) => {
                    if (value === "randomize") {
                        value = "populate";
                        setWidgetValue(node ?? this, modeWidget, "populate");
                    }

                    if (populatedTextWidget?.inputEl) {
                        populatedTextWidget.inputEl.disabled = value === "populate";
                    }

                    originalModeCallback?.(value, canvas, node, pos, e);
                };

                if (populatedTextWidget?.inputEl) {
                    populatedTextWidget.inputEl.disabled = modeWidget.value === "populate";
                }
            }

            if (wildcardSelectWidget) {
                this._wildcard_value = "Select the Wildcard to add to the text";

                wildcardSelectWidget.callback = async (value, canvas, node) => {
                    const targetNode = node ?? this;
                    appendWildcard(targetNode, targetNode._wildcard_value);

                    if (wildcardStatus.onDemandMode) {
                        await loadWildcardStatus();
                        await loadWildcards();
                        app.canvas.setDirty(true, true);
                    }
                };

                Object.defineProperty(wildcardSelectWidget, "value", {
                    set: (value) => {
                        if (!isSelectLabel(value)) {
                            this._wildcard_value = value;
                        }
                    },
                    get: () => {
                        return wildcardLabel();
                    },
                });

                Object.defineProperty(wildcardSelectWidget.options, "values", {
                    set: () => {},
                    get: () => {
                        return wildcardsList;
                    },
                });

                wildcardSelectWidget.serializeValue = () => {
                    return "Select the Wildcard to add to the text";
                };
            }

            return result;
        };
    },
});