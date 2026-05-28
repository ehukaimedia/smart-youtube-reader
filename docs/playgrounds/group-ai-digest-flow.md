# Group AI Digest Flow

```mermaid
flowchart TD
    A["Dashboard completed projects"] --> B["User selects projects for group"]
    B --> C["Copy Group AI Digest CLI Task"]
    C --> D["External agent reads all archives"]
    D --> E["External agent inspects source frame images as evidence"]
    E --> P["CLI payload surfaces preservation_items per source chapter"]
    P --> F["Agent writes novel transcript with facts, theory, hypotheses"]
    F --> G["Agent creates exactly 3 novel WebP teaching images"]
    G --> H["CLI validates draft and image files"]
    H --> I["New clean data/jobs project"]
    I --> J["archive.json uses only generated image paths"]
    I --> K["manifest.json kind=group_ai_digest"]
    K --> L["Dashboard badge + Tailscale link"]
    J --> M["Reader shows novel transcript with generated images"]
```

## Key Architecture Rule

Single-video text-only AI digests may preserve source frame references for human curation. Default single-video AI digests and group AI digests use generated WebP teaching images. Group source images are evidence only; the materialized group project contains only the three new generated WebP teaching images.
