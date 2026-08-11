import { describe, expect, it } from "vitest";

import { UI_COMPONENTS } from "./ui";

const sourceModules = import.meta.glob("../**/*.vue", {
  eager: true,
  import: "default",
  query: "?raw"
});

const TAG_OVERRIDES = {
  FormItemGridItem: "n-form-item-gi"
};

function componentTag(component) {
  if (TAG_OVERRIDES[component.name]) return TAG_OVERRIDES[component.name];
  return `n-${component.name.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase()}`;
}

describe("Naive UI component registry", () => {
  it("matches every n-* component used by Vue templates without unused global imports", () => {
    const usedTags = new Set(
      Object.values(sourceModules).flatMap((source) => source.match(/<n-[a-z0-9-]+/g) || [])
    );
    const registeredTags = new Set(UI_COMPONENTS.map(componentTag).map((tag) => `<${tag}`));

    expect([...registeredTags].sort()).toEqual([...usedTags].sort());
  });
});
