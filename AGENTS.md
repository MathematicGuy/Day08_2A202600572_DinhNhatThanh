<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

<!-- BEGIN:error-context-engineering-rules -->
# Error Context Engineering Protocol

Whenever you encounter a runtime, build, or testing error, you must follow this workflow:

1. **Check `ERROR/index.md`**: Before taking any action, immediately view [ERROR_LOG/index.md](ERROR_LOG/index.md) to check if the error is already documented.
2. **If the error is ALREADY documented**:
    * View the corresponding documentation file (e.g. `ERROR_LOG/[Error_Name]_ERROR.md`) to learn the root cause, verified solutions, and paths to avoid.
    * Apply the documented solutions and verify.
    * If the error **still persists after 2 consecutive retries or test runs**, proceed to step 3 to perform context engineering and update/expand the documentation.
3. **If the error is NEW, or still persists after 2 retries on a documented error**:
    * Trigger the `/context-engineering` skill in (.agents\skills\context-engineering) with this exact prompt format:
      ```
      /context-engineering context engineer the [Error_Name] error into a ERROR_LOG/[Error_Name]_ERROR.md so CODEX understand the full scope of the error and which path it should avoid re-trying or re-testing
      ```
    * Create or update the corresponding error markdown file under `ERROR_LOG/`.
    * Update [ERROR_LOG/index.md](ERROR_LOG/index.md) to register the new/updated error file.
<!-- END:error-context-engineering-rules -->
