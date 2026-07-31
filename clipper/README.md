# Research Assistant Clipper (browser extension)

Clips selected text — or the whole page as a bookmark — into your local
Research Assistant inbox, with the source URL and page title attached
automatically. Works while the app (or just the backend) is running on
`127.0.0.1:8734`.

## Install (Chrome / Edge / Brave)

1. Open `chrome://extensions` (or `edge://extensions`)
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and select this `clipper/` folder

## Use

- **Toolbar popup** — review/edit the clip before saving; tick *Save as task*
  to send it to your task list instead of the inbox.
- **Right-click → "Clip to Research Assistant"** — one-shot clip of the
  selection (or the page, if nothing is selected). A ✓ badge confirms.
- **Alt+Shift+C** — same one-shot clip from the keyboard.

Everything lands in the app's Inbox for triage, except *Save as task* clips
(and any clip starting with `todo:`), which become tasks — natural-language
dates and `#project` / `p1` / `@tag` markers all work.
