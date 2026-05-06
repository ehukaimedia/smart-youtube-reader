# Project ZIP Download Plan

## Steps

1. Replace the placeholder `/jobs/{job_id}/download` response with a real ZIP response.
2. Build the ZIP from the resolved job directory and guard it under `data/jobs`.
3. Store the temporary ZIP outside the project tree and delete it after the response.
4. Update the reader page action to call `/jobs/{job_id}/download`.
5. Add copyable project links on both dashboard cards and the project page.
6. Verify the backend endpoint returns a ZIP containing the job folder and generated files.
