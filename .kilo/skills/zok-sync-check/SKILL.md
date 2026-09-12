---
name: sync-check
description: >-
  Use this skill when you need instructions on how to validate integration statuses,
  Shopify order webhooks, or test WhatsApp/LINE OA CRM sync parameters.
---

# Zaapi Integration Sync Verification Skill

This skill contains instructions and workflows for validating channels integrations, syncing customer profiles, and verify order history triggers.

## Verification Steps

### 1. Shopify Order History Sync
1. Open the [Integrations Portal](file:///mnt/zok/src/views/Dashboard/Integrations.jsx) and toggle the **Shopify Store Sync** switch.
2. Review the live log output console. Ensure you see:
   * `Shopify integration initialized... Sync status: OK`
   * `Synced active products`
3. Navigate to [Unified Inbox](file:///mnt/zok/src/views/Dashboard/UnifiedInbox.jsx) and select **Karmart Customer Support**.
4. Confirm that the CRM panel displays Order IDs, Dates, Prices, and Status (e.g. `ORD-5512` - Shipped).

### 2. Live Channel Webhooks
1. In the integrations panel, verify webhook event subscription records.
2. Toggle the channel switches (Shopee, Lazada, TikTok Shop) and confirm matching connection sync records write to the sync log console.
3. In the visual flow builder, ensure conditions target the correct tag (e.g., checking if tag matches `Shopify Buyer`).
