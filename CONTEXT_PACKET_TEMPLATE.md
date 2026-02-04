# Context Packet Template (PCP-lite)

- **Project:** <project name, optional>
- **Stage:** <stage number or label, optional>
- **Substage:** <substage identifier, optional>
- **Version:** <schema/template version, optional>

## Mission
- <succinct mission statement>

## Current Reality (Facts Only)
- <fact 1>
- <fact 2>
- ...

## Constraints
- <constraint 1>
- <constraint 2>
- ...

## Acceptance / Definition of Done
- <acceptance criterion 1>
- <acceptance criterion 2>
- ...

## Required Artifacts
- <artifact 1>
- <artifact 2>
- ...

## Failure Modes
- <known risk, anti-goal, or non-goal 1>
- <known risk, anti-goal, or non-goal 2>
- ...

## Substage Gate / Work Envelope
- <what is allowed or in-scope for this substage>
- <what is explicitly out-of-scope>

## Notes or Scope Warnings (Optional)
- <note 1>
- <note 2>

## Sources of Truth (Optional)
- <link or reference 1>
- <link or reference 2>
- ...

## Risk Flags (Optional)
- <risk flag: high_blast_radius | needs_human_signoff | missing_info | network_required | destructive_action | secrets_involved | external_dependency>

## Allowed Actions (Optional)
- <action: git_read | git_write | filesystem_read | filesystem_write | http_read | http_write | docker | shell_exec | secrets_read | database_read | database_write>

## Evidence Requirements (Optional)
- <evidence type: pr_link | commit_sha | test_output | diff | logs | screenshot | artifact_path | api_response>

---

**Usage Notes**
- Keep each bullet factual, testable, and concise.
- Maintain section order; do not omit required sections even if a list is brief.
- Align field names and content with `pcp_lite.schema.json`.
- Update `Version` when the schema or template meaning changes.
- If a field is intentionally empty, state why rather than omitting it.
