![AdeptAds](assets/logo.svg)

# AdeptAds Google Ads

**Ship your product. Launch its campaigns.**

Tell your agent what you sell and who should see it. AdeptAds takes care of the campaign build.

AdeptAds multi-agent workflows build complete, tightly targeted campaigns: several themed ad groups or asset groups, each with researched keywords, multiple ads and images where the campaign type needs them. Choose Search, Display or Performance Max in the Google Ads account you pick. New campaigns arrive paused. You look them over and decide when they go live.

Already running ads? Grow a campaign with new ad groups, keywords, search themes or locations. Read results, pause or resume, and change budgets or bidding in the same conversation. Additions to a live campaign can start serving right away; new locations wait for your approval in the AdeptAds dashboard.

Free to install. To run it you need an AdeptAds account with trial or paid-plan credits and a connected Google Ads account. Google bills ad spend separately. Autopilot is set up in the AdeptAds dashboard.

### Try it

- "Build a Search campaign for my website. Help me choose the audience and budget."
- "Find useful keywords to add to this campaign. Show me the scope before making changes."
- "Show my campaign results for the last 30 days and suggest what to do next."

### Get connected

```sh
codex plugin marketplace add adeptads/agent-skills
codex plugin add adeptads-google-ads@adeptads
```

Start a new session and complete AdeptAds OAuth sign-in when prompted.

Connect Google in AdeptAds and choose the intended Google Ads account before making changes.

### Your data and control

This package connects your agent to the hosted AdeptAds MCP service at https://api.adeptads.ai/mcp. Your requests and relevant account and campaign context are sent to AdeptAds to run the selected tools and workflows against your connected Google Ads account. Authentication uses AdeptAds OAuth; keep credentials out of chat.

AdeptAds emails the account owner about agent-triggered starts, bidding strategy changes, removed limits, large spend-related increases, and changes it could not verify. Alerts do not replace your approval.

[Support](https://www.adeptads.ai/#about-contact) · [Privacy](https://www.adeptads.ai/privacy-policy) · [Terms](https://www.adeptads.ai/terms-of-service) · [Source](https://github.com/adeptads/agent-skills) · [MIT license](LICENSE)

The license covers this client package. The hosted AdeptAds service remains subject to its own terms and billing.
