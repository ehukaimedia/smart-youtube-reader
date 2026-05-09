# Dashboard YouTube Thumbnails Plan

## Steps

1. Parse YouTube video IDs from each dashboard job's `video_url`.
2. Build a public `i.ytimg.com` thumbnail URL from the parsed ID.
3. Render a fixed-aspect thumbnail area at the top of each project card.
4. Keep a fallback thumbnail surface for malformed or missing URLs.
5. Update the architecture playground note for dashboard card responsibilities.
