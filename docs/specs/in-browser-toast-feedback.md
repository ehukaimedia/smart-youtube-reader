# In-Browser Toast Feedback Spec

## Context

Native browser `alert()` and `confirm()` dialogs are hard for automation agents to inspect and interact with consistently. User-visible feedback and confirmations should live in the app DOM.

## Expected Behavior

All user alerts, errors, success messages, and destructive-action confirmations should render as in-browser toast UI.

Confirmation toasts must:

- Stay visible until the user chooses an action.
- Provide explicit confirm and cancel buttons.
- Resolve the calling workflow only after a button is clicked.
- Use accessible roles so browser automation can identify them.

## Non-Goals

- Do not use native `alert()` or `confirm()`.
- Do not require route-specific toast implementations.
