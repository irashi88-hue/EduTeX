# EduTeX local course studio (MVP slice 1)

Start the local browser editor for an existing course project:

```powershell
edutex author studio --project .
```

The first slice edits course metadata and the ordered module/lesson structure in
`course.yaml`. It leaves linked lesson Markdown files untouched. The editor binds
only to `127.0.0.1`, uses a per-run token, preserves fields it does not edit, and
validates a temporary manifest before atomically replacing the original. YAML
formatting and comments may be normalized on save. Press Ctrl+C in the terminal
to stop the local server.
