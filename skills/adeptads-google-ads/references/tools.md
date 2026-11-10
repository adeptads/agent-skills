# AdeptAds MCP tool contract

Use the live `tools/list` schemas for exact types and supported values. These are AdeptAds tool names; a client may prepend a server namespace. This reference does not grant permission to mutate an account.

## Account references

Every campaign tool requires `account`, an object copied from `accounts[*].account_ref` in the selected account listing:

```json
{
  "account_id": "<account UUID from listing>",
  "access_root_id": "<access-root UUID from listing>",
  "platform_auth_id": "<platform-auth UUID from listing>",
  "credential_version": 1
}
```

The version above is illustrative: copy the actual positive integer returned by the server. These UUIDs are AdeptAds route identifiers, not Google customer IDs. Keep the account and credential route together. Never build a reference from dashboard settings.

## Tools

| Tool | Arguments | Use |
| --- | --- | --- |
| `get_connection_status` | None | Signed-in connection, plan, credits and granted scopes. Follow returned actions if blocked. |
| `list_accounts` | Omit both IDs for roots; supply both `manager_id` and `access_root_id` for children | Discover roots, managers and accessible accounts. Traverse using returned identifiers. |
| `refresh_accounts` | Required `idempotency_key`; omit both or supply both `manager_id` and `access_root_id` | Refresh accessible accounts. Poll its task receipt before listing again. |
| `get_campaign_setup_options` | `account`, `channel` (`SEARCH`, `DISPLAY`, `PERFORMANCE_MAX`) | Conversion catalog with `conversions_last_30_days` per action (null when unavailable), account `currency_code`, and bidding policy. No credit use or campaign change. |
| `resolve_geo_target` | `account`, `request` with `name`; optional `country_code`, `place_type`, `parents` | Resolve a place to one canonical Google target name/ID. Names and parents are English; `locale` is ignored. Check the returned country and type before use. |
| `list_campaigns` | Required `account`; optional `sync` (default `true`), `campaign_status` | Campaigns for this account. Sync refreshes reporting metadata only. |
| `get_campaign` | `account`, `campaign_id` | Current status, creation outcome, `bidding_strategy`, `bidding_status`, and `serving`: `currency_code`, `daily_budget_amount`, current included/excluded locations with names, radius and location-group counts, `location_setting`, and `networks` for Search and Display (`google_search`, `search_partners`, `display_network`, `ai_max` for Search; null for other channels). `content` lists each ad or asset group with its status, keyword and ad (or asset) counts and first 3 headlines, plus `approval` counts (`approved`, `limited`, `under_review`, `disapproved`, `unknown`) of its `approval_of` items. `geography_error`, `networks_error` and `content_error` replace parts that could not be read. |
| `get_campaign_performance` | `account`, `campaign_id`; optional `period`, `start_date`, `end_date` | `period`: `last_7_days` (default), `last_30_days`, `today`, `yesterday`, `custom`. `custom` needs both dates, 1-90 days, ending no later than today in the account time zone; the comparison period must fall within 3 years. Unpublished campaigns return 409. |
| `create_campaign` | `account`, `request`, `idempotency_key` | Build and publish a campaign. It is always created `PAUSED`. |
| `set_campaign_status` | `account`, `campaign_id`, `status`, `idempotency_key` | Set `ENABLED` or `PAUSED`. `ENABLED` starts spend and is rejected (409) while the campaign is still being built. Returns a synchronous receipt, not a task. |
| `update_campaign_budget` | `account`, `campaign_id`, `daily_budget_amount`, `currency_code`, `idempotency_key` | Set the average daily budget. `currency_code` must equal the account currency; a mismatch is rejected before the key is used. Synchronous receipt. |
| `update_campaign_bidding` | `account`, `campaign_id`, `request`, `idempotency_key`; `currency_code` with any CPC or CPA amount | `request` is `{"bidding_strategy": {"type", "config"}}` with account-currency amounts. For Maximize Clicks, use `bidding_strategy.config.max_cpc_amount`, matching setup options. The optional top-level `request.max_cpc_amount` is also accepted; do not send both forms. `currency_code` must equal the account currency. Omitting a target removes the current one. `max_cpc_amount` is only for Maximize Clicks. Manual CPC is rejected before the key is used. Synchronous receipt. |
| `expand_campaign` | `account`, `campaign_id`, `expansion_type`, `brief`, `idempotency_key`; optional `max_new_keywords`, `target_group_ids` for CONTENT | UNIT/CONTENT publish directly; TARGETING returns a proposal for dashboard approval. |
| `get_task_status` | `task_id`; optional `wait_seconds` (0-30) | Read a creation, expansion or refresh task issued to this user and MCP grant. With `wait_seconds`, the call returns when the status or step changes, the task ends, or the time runs out. While a creation runs, `progress` gives `last_completed_step`, `step_index` of `step_count` and `updated_at` (null before the first step finishes). |

`campaign_id` is the AdeptAds campaign UUID returned by these tools, never a Google resource ID.

## Performance values

Each period has `totals` and `days`. `cost` is in the response `currency_code`; `cost_micros` is the raw value. Every day in the window is listed; `reported=false` means Google reported no activity that day. `includes_today` marks a partial day. Interpretation rules are in [PPC checks](ppc-checks.md#reading-performance).

## Creation request

`request` follows `CampaignCreateRequest`:

| Field | Contract |
| --- | --- |
| `target_url` | The operator's website URL. |
| `advertising_channel_type` | `SEARCH`, `DISPLAY` or `PERFORMANCE_MAX`. |
| `campaign_goal` | `BRAND_AWARENESS`, `LEAD_GENERATION` or `SALES`. |
| `conversion_selection` | `account_default` (default), or `selected_actions` with `action_resource_names` copied from setup options. |
| `geo` | `inclusions` list; optional `exclusions`, `inclusion_ids`/`exclusion_ids` from `resolve_geo_target`, and radius targeting per schema. |
| `daily_budget_amount`, `currency_code` | Positive daily amount. `currency_code` must equal the account currency from setup options; a mismatch (422) or an unknown account currency (409) is rejected before the key is used. Not a total campaign cap. |
| `campaign_mode` | `STRICT` keeps strategy within the supplied audiences and geography; `CREATIVE` allows broader suggestions. Prefer `STRICT` when boundaries are fixed. |
| `bidding_strategy` | Supported `type` and optional `config` from the bidding policy. |
| `max_cpc_amount` | Required for `MANUAL_CPC`. For `MAXIMIZE_CLICKS`, set the ceiling in `bidding_strategy.config.max_cpc_amount` instead. Omit for conversion-based strategies. |
| `project_description` | Optional offer keypoints in the operator's own words or chosen from sourced candidates. |
| `target_users` | Optional audience keypoints in the operator's own words or chosen from sourced candidates. `STRICT` keeps segments to this audience; `CREATIVE` starts from it. Empty: AdeptAds infers the audience from the site. Never send inferred text. |
| `content_language` | Optional; inferred when omitted. |

Creation uses AdeptAds creation credits. The campaign does not serve until `set_campaign_status` `ENABLED`.

Setup options list enabled conversion actions with owner, primary/secondary status, account-default membership and 30-day volume. Copy full resource names: the owner can be a manager account. With `selected_actions`, every selected action is used for bidding through a custom goal, even a secondary one; account-wide settings do not change.

The bidding policy uses creation-request config names and account-currency amounts, not micros. `enabled` means supported for that channel; `requires_conversions` still depends on the conversion selection. `required_request_fields` lists top-level inputs such as `max_cpc_amount` for Manual CPC. For a Search CPA target, use `MAXIMIZE_CONVERSIONS` with `config.maximize_conversions_target_cpa`.

Location resolution returns one best match. Supply country, place type and parent areas to disambiguate. This tool does not geocode street addresses or control presence-versus-interest targeting.

## Expansion request

`expand_campaign` needs the complete `account`, the AdeptAds `campaign_id`, an `expansion_type`, a nonblank `brief` of 1-4000 characters, and a stable `idempotency_key`. Optional `max_new_keywords` (1 or more) and `target_group_ids` apply only to `CONTENT_EXPANSION`; other types return 422. Copy group IDs from `get_campaign` → `content.groups`. If the operator names specific groups, pass their IDs; otherwise omit the selector and let the workflow choose. Unknown groups are rejected before credits are claimed.

| Expansion type | Outcome |
| --- | --- |
| `UNIT_EXPANSION` | At most one justified new ad group or asset group. New ads may serve at once on an enabled campaign. Can end `NO_CHANGE`. |
| `CONTENT_EXPANSION` | Additional keywords or search themes in existing groups. Keywords that fail the offer review are dropped. `max_new_keywords` caps the additions, keeping the highest-volume reviewed Search/Display keywords; it also caps PMax search themes. Omitted means no requested cap. Themes go through offer review; themes already on the asset group are skipped, and Google allows 50 per asset group. Can end `NO_CHANGE`. |
| `TARGETING_EXPANSION` | Research locations and return a proposal for dashboard approval. Research alone does not publish. Can end `NO_CHANGE`. |

Prerequisites: the campaign must be published to Google Ads (412 otherwise), and a SEARCH or DISPLAY campaign needs a saved bidding strategy for UNIT/CONTENT (412 otherwise). `target_group_ids` selects existing groups for CONTENT only; it does not set group bids or budgets. Expansion has no budget argument.

Expansion uses optimization credits, separate from creation credits. Geographic research needs an active subscription and a positive optimization allowance but does not debit a credit; approval checks the allowance again. A proposal awaiting approval expires after 7 days. Expansion does not enable or configure Autopilot.

## Mutation receipts and polling

Create, expand and refresh return a task receipt. Keep its `task_id`, trace and operation identifiers, `status` and `dispatch_state`. Expansion receipts also carry `action_log_id`, `campaign_id` and `expansion_type`.

An idempotency key is bound to the MCP grant, the exact payload, and the exact `account_ref` including `credential_version`. Every receipt carries a `retry_policy`; follow it first.

| Situation | Agent action |
| --- | --- |
| Uncertain call result (timeout, no receipt) | Retry with the same key and inputs. |
| Rejected before a receipt: 402 billing or credits, 422 validation or currency mismatch, 409 unknown account currency | Nothing was stored. Fix the cause (billing, input, or `refresh_accounts` for currency), then retry; the same key still works. |
| Receipt with `dispatch_state=failed` and a `retry_policy` naming a new key | Nothing was dispatched. Fix the reported problem, then send the corrected request with a new key. |
| Worker failure `KEYWORD_COVERAGE_INSUFFICIENT` | Nothing was published. Agree a changed brief with the operator (broader offer, market or keywords, or a different channel such as Performance Max), then use a new key. |
| Worker failure `WEBSITE_EVIDENCE_UNAVAILABLE` | Nothing was published. The site could not be read and the request had no business description. Ask the operator for a short description of the offer, or a publicly readable URL, then use a new key. |
| 409 conflict on a key | The key was reused with different inputs, account route or grant. For a deliberate change after a failed receipt, use a new key. Otherwise inspect with `list_campaigns`/`get_campaign`; never re-dispatch an action that may already have run. |
| Google reconnected or MCP connection replaced | Run `list_accounts` for a fresh `account_ref`. Earlier tasks may be unreadable: keep their IDs, inspect the campaign, report the access error. Never reuse an old key with the new reference. |
| `dispatch_unknown` | Delivery is uncertain, not failed. Keep polling or inspect the campaign; never send a replacement. |
| 409 on `ENABLED`, budget or bidding while building | Wait for creation to finish, then ask again. |

`set_campaign_status`, `update_campaign_budget` and `update_campaign_bidding` return `completed` with `campaign`, `failed` when rejected before reaching Google (such as a bidding policy error; the retry policy names a new key), or `dispatch_unknown`, which carries `google_error` and `google_request_id` when Google returned an error. After `dispatch_unknown`, read the campaign before any new change. They have an operation ID and no task ID. A `completed` receipt carries `spend.owner_alerted`: AdeptAds emails the ad account owner when an agent enables a campaign, changes the bidding strategy, removes all bidding targets and caps, or moves the daily budget, target CPA or CPC cap above twice (target ROAS below half) its value before the agent's run of changes. The owner is also emailed when a spend change cannot be confirmed. Mention a non-empty `owner_alerted` in the result; it is not an error.

## Task states

Polling is client-driven; nothing is pushed into a closed chat. Read `status`, `ready`, `successful`, `failed`, `dispatch_state`, and the result fields together.

| Signal | Terminal | Agent action |
| --- | --- | --- |
| `ready=false` (`PENDING`, `STARTED`, `RETRY`, `IN_PROGRESS`) | No | Call again with `wait_seconds: 30`; the server waits for a change or timeout. Report `progress.last_completed_step` when it changes. Follow the skill's 30-minute handoff limit. |
| `PENDING_APPROVAL` (`ready=true`, `successful=false`, `failed=false`) | Paused | Validate and show `review_url` with `targeting_plan`; stop polling until the operator says they decided, then poll the same `task_id`. |
| Creation `SUCCESS` with `result_available=true` | Yes | Report the typed `result`; then ask to start the campaign. |
| Creation `SUCCESS` with `result_available=false` | Yes | Older outcome without a result: read `get_campaign` and report from it. |
| `refresh_accounts` `SUCCESS` | Yes | Run `list_accounts` again. |
| Expansion `status=SUCCESS`, `overall_status=EXECUTED` | Yes | Report `persisted_resources` per operation. |
| `PARTIAL_SUCCESS` | Yes | Report published parts, failures and `gaps`; never re-run to fill gaps. For creation, ask to start only after the operator has seen the gaps. |
| `NO_CHANGE` (`ready=true`, `successful=false`, `failed=false`) | Yes | Report the rationale. Not a failure; UNIT/CONTENT credit is restored. |
| `REJECTED` or `EXPIRED` (targeting) | Yes | Report the dashboard decision; do not resubmit. |
| `FAILED` / `FAILURE` / `REVOKED` | Yes | Report the error category and step, and follow `retry_policy` if present. Failure alone does not prove no provider writes happened; read the campaign. |
| `OUTCOME_UNCONFIRMED` / `OUTCOME_UNAVAILABLE` | Yes | Read `get_campaign`, report the uncertainty, never create a replacement. |

Creation outcomes come from the saved operation record (`outcome_source="creation_operation"`) and describe the original run even after a later dashboard resume; use `get_campaign` for the current state and resume availability. Older operations may use `outcome_source="creation_receipt"` with `result_available=false`. Worker failures before a campaign exists use `outcome_source="worker_failure"`. `creation_summary` can include `failures`, `gaps` and `can_resume`; this package has no resume tool.

Expansion tasks expose `expansion_summary` (`overall_status`, `attempted`, `succeeded`, `failed`, `operations`), `action_status` and `execution_error`. The internal `action_status=REJECTED` on a `NO_CHANGE` run is not a failure.
