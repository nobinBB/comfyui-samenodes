import { app } from "../../scripts/app.js";

// Overrides fonts with Noto Sans JP.
// Some extensions bundle Chinese fonts that override the system font stack,
// making Japanese glyphs render with Chinese variants (different stroke design).
// Injecting this style last forces Noto Sans JP across all HTML elements and
// also remaps "Arial" (used by LiteGraph canvas rendering) to Noto Sans JP
// for CJK codepoints.

app.registerExtension({
    name: "comfyui.samenodes.FontOverride",

    setup() {
        // Preconnect to speed up Google Fonts loading
        for (const href of ["https://fonts.googleapis.com", "https://fonts.gstatic.com"]) {
            const l = document.createElement("link");
            l.rel = "preconnect";
            l.href = href;
            if (href.includes("gstatic")) l.crossOrigin = "anonymous";
            document.head.appendChild(l);
        }

        // Load Noto Sans JP
        const fontLink = document.createElement("link");
        fontLink.rel = "stylesheet";
        fontLink.href =
            "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap";
        document.head.appendChild(fontLink);

        // Inject override CSS into <body> so it is added after all other
        // extension styles (later in the cascade wins for equal specificity)
        const style = document.createElement("style");
        style.id = "samenodes-font-override";
        style.textContent = `
            /* Remap Arial in CJK range so LiteGraph canvas text also uses Noto Sans JP */
            @font-face {
                font-family: "Arial";
                src: local("Noto Sans JP");
                unicode-range: U+3000-9FFF, U+F900-FAFF, U+FF00-FFEF, U+AC00-D7AF;
            }

            /* Override specific UI elements only - avoid affecting colors/layout */
            body,
            input,
            textarea,
            button,
            select,
            option,
            .comfy-menu,
            .comfy-modal,
            .litegraph {
                font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Meiryo",
                             sans-serif !important;
            }
        `;

        const inject = () => document.body.appendChild(style);
        if (document.body) {
            inject();
        } else {
            document.addEventListener("DOMContentLoaded", inject);
        }
    },
});
