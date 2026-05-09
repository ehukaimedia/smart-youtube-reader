# In-Browser Toast Feedback Plan

## Steps

1. Add a shared client-side toast provider at the app layout level.
2. Expose notification helpers for info, success, and error states.
3. Expose a promise-based confirmation helper for destructive or redirecting workflows.
4. Replace all native `alert()` and `confirm()` calls in frontend pages.
5. Verify agents can see and click confirmation toast buttons in the browser DOM.
