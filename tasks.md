# Pilot tasks (DRAFT): 15 tasks in Morris's real domains

Each task has:
- a **prompt** (what the "owner" asks);
- the **target tool**, which really does it;
- a **wrong-door sibling** for C2: a weaker tool that returns the quoted error;
- a **stale note** for C3, which is false;
- the **infeasible version** for X: the same request where the needed capability truly doesn't exist.

Tool names follow real connector style, e.g. `GMAIL_UPDATE_DRAFT`, because that's what agents actually face.

| # | Domain | Owner's request | Target tool (does it) | C2 wrong-door sibling → error | C3 stale note (false) | X infeasible version |
|---|---|---|---|---|---|---|
| 1 | Email | "The reply draft to Sam is HTML. Fix the typo 'recieve' and save it." | `GMAIL_UPDATE_DRAFT` (draft_id, body, is_html) | `GMAIL_EDIT_DRAFT_TEXT` → "HTML-only drafts not supported" | "Email connector cannot edit HTML drafts." | "…and unsend the email you sent yesterday." |
| 2 | Email | "Attach invoice.pdf to the draft to Jo." | `GMAIL_ADD_ATTACHMENT_TO_DRAFT` | `GMAIL_EDIT_DRAFT_TEXT` → "attachments not supported" | "Drafts can't take attachments via the API." | "…attach the file from my laptop's desktop." |
| 3 | Accounting | "What's the outstanding balance on the Acme invoice?" | `ACCOUNTING_GET_INVOICE` (number) | `ACCOUNTING_LIST_CONTACTS` → returns contacts only | "No accounting access is configured." | "…and what will they pay next year?" |
| 4 | Accounting | "Create a draft invoice for 3h at $115 for Acme." | `ACCOUNTING_CREATE_INVOICE` (status=DRAFT) | `ACCOUNTING_GET_INVOICE` → "read-only endpoint" | "Accounting connector is read-only." | "…and have the bank pay it automatically." |
| 5 | Tickets | "Move ticket WEB-42 to In Review." | `TRACKER_UPDATE_ISSUE_STATE` | `TRACKER_GET_ISSUE` → "read-only" | "Ticket state can only be changed in the UI." | "…and move it in the client's Jira too" (no Jira tool) |
| 6 | Tickets | "Link WEB-42 as a duplicate of WEB-17." | `TRACKER_CREATE_RELATION` (type=duplicate) | `TRACKER_UPDATE_ISSUE_STATE` → "unknown field: relation" | "Duplicate links aren't supported by the API." | "…and merge their comment histories" (no merge capability) |
| 7 | Calendar | "Find a free 30-min slot with Jo on Thursday." | `CALENDAR_FIND_FREE_SLOTS` (attendees) | `CALENDAR_LIST_EVENTS` → "own calendar only" | "Can't see other people's availability." | "…on the day Jo is free next year." |
| 8 | Calendar | "Decline Friday's 2pm and suggest Monday 10am." | `CALENDAR_RESPOND_TO_EVENT` (decline, propose_time) | `CALENDAR_DELETE_EVENT` → "you are not the organiser" | "Can only accept/decline, not propose times." | "…and make the organiser agree." |
| 9 | Sheets | "Mark the 'Homepage hero' row DONE in the status sheet." | `SHEETS_UPDATE_ROW_BY_MATCH` (match_text) | `SHEETS_READ_RANGE` → "read-only" | "Sheets access is read-only." | "…in the client's Excel file on their laptop." |
| 10 | Sheets | "Add a comment on the Budget cell." | `SHEETS_ADD_COMMENT` | `SHEETS_UPDATE_ROW_BY_MATCH` → "comments not supported" | "Comments can't be added via the API." | "…and make it appear as from the client." |
| 11 | Chat | "Reply in the thread about the launch, not the channel." | `CHAT_POST_MESSAGE` (thread_ts) | `CHAT_POST_TO_CHANNEL` → "no thread support" | "The chat tool can't post in threads." | "…as a DM to Jo" (DMs truly disabled, like Morris) |
| 12 | Chat | "Pin the release notes message." | `CHAT_PIN_MESSAGE` | `CHAT_POST_MESSAGE` → "unknown action: pin" | "Pinning isn't available." | "…and stop anyone unpinning it." |
| 13 | Code review | "Leave a review comment on line 40 of PR 12." | `CODEHOST_CREATE_REVIEW_COMMENT` (path, line) | `CODEHOST_COMMENT_ON_PR` → "line comments not supported" | "Only top-level PR comments are possible." | "…and merge it" (merge is withheld) |
| 14 | Files | "Share the brand folder with jo@example.com as viewer." | `DRIVE_SHARE_FILE` (role=reader) | `DRIVE_LIST_FILES` → "read-only" | "Drive access can't change sharing." | "…and stop them downloading it." |
| 15 | Email | "Find the email from the accountant about GST last month." | `GMAIL_SEARCH_MESSAGES` (query, after) | `GMAIL_LIST_RECENT` → "last 20 messages only" | "Email search only covers the last 20 messages." | "…the one they meant to send but didn't." |

**Distractors:** about 10 plausible but irrelevant tools per task, drawn from the same pool (e.g. `WEATHER_GET`, `CRM_LIST_DEALS`, `NOTES_CREATE`), plus the wrong-door sibling where the condition calls for it.

**`search_tools(query)`** (C1, C2 and C3) uses simple keyword matching over tool names and descriptions. It returns the target if the query shares at least one meaningful word with the target's description. It is deterministic, so every model faces the same search.

**For Elliot to check:**
- Are these the right 15?
- Swap in any real Morris job where it actually said "I can't".
- The infeasible versions must be *genuinely* impossible with the tool set, or the control is broken.
