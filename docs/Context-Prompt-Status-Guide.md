# Context Prompt Status Indicator - User Guide

**Last Updated:** 2026-01-22

---

## Overview

The Context Prompt feature now includes a **real-time status indicator** that shows whether your system prompt is saved and active. This gives you immediate visual feedback about the state of your prompt.

---

## Status Indicators

The status label appears directly below the Context Prompt text box and shows one of three states:

### 1. ⚠ No Prompt Configured
**When shown:** No text in the prompt box
**Color:** Gray (muted)
**Meaning:** You haven't configured a custom prompt. The AI will use default behavior.

```
⚠ No prompt configured - using default behavior
```

### 2. ✓ Prompt Active
**When shown:** Text in box matches saved prompt
**Color:** Green (success)
**Meaning:** Your custom prompt is saved and will be used for all new conversations.

```
✓ Prompt active (2,247 characters)
```

### 3. ✎ Modified
**When shown:** Text in box differs from saved prompt
**Color:** Orange (warning)
**Meaning:** You've made changes that aren't saved yet. Scroll down and click Save Settings.

```
✎ Modified (2,350 characters) - click Save to apply
```

---

## How to Use

### Step 1: Open Settings
Click the **⚙️ Settings** button in the top-right corner of the GUI.

### Step 2: Find Context Prompt Section
Scroll through the Settings dialog until you see:

```
Context Prompt
System prompt prepended to all new conversations (scroll down to save)
```

### Step 3: Enter Your Prompt
Paste or type your system prompt into the text box. You can use the recommended prompt from:

📄 `docs/system-prompt.txt`

### Step 4: Check the Status
Look at the status label below the text box:
- If it shows **✎ Modified**, your changes aren't saved yet
- The character count updates as you type

### Step 5: Save Your Settings
**IMPORTANT:** Scroll to the bottom of the Settings dialog and click **Save Settings**.

The Save Settings button is at the very bottom, below:
- Context Prompt
- OSINT API Keys
- MCP Servers (if configured)
- Learning Settings (if enabled)

### Step 6: Verify Saved
Reopen Settings and check the Context Prompt section. The status should show:

```
✓ Prompt active (X,XXX characters)
```

This confirms your prompt is saved and will be applied to all new conversations.

---

## Important Notes

### Applies to New Conversations Only
The context prompt is prepended to the conversation when you:
- Start a new chat (click **New Chat** button)
- Restart the application

It does **NOT** affect:
- Existing conversations (already in progress)
- Previous messages in current session

### Character Count
The status shows the total character count of your prompt. Typical recommended prompts are:
- **Basic:** 500-1,000 characters
- **Detailed:** 1,500-2,500 characters
- **Comprehensive:** 3,000+ characters

The example prompt in `docs/system-prompt.txt` is approximately **2,247 characters**.

### Real-Time Updates
The status updates automatically as you type:
- Character count changes immediately
- Status changes from "✓ Active" to "✎ Modified" when you edit
- Status returns to "✓ Active" after saving (when you reopen Settings)

---

## Troubleshooting

### "I don't see the Save Settings button"
**Solution:** Scroll down in the Settings dialog. The Save Settings button is always at the bottom, below all configuration sections.

### "The status says Modified but I haven't changed anything"
**Possible causes:**
- Extra whitespace at beginning/end (gets trimmed on save)
- Line ending differences (Windows vs Unix)

**Solution:** Click Save Settings anyway - it will normalize the formatting.

### "My prompt isn't working in conversations"
**Checklist:**
1. ✓ Status shows "✓ Prompt active" when you open Settings
2. ✓ You've started a NEW conversation (not continuing old one)
3. ✓ The prompt defines clear behavior instructions

**Test:** Start a new conversation and ask the AI: "What are your core responsibilities?"

If the prompt is active, it should respond based on your custom instructions.

### "The status disappeared"
**Cause:** This shouldn't happen - the status label is always present.

**If it does happen:** Close and reopen Settings. If the issue persists, check for errors in the console.

---

## Example Workflow

### First-Time Setup
1. Open Settings → Context Prompt
2. See: `⚠ No prompt configured - using default behavior`
3. Copy text from `docs/system-prompt.txt`
4. Paste into Context Prompt box
5. See: `✎ Modified (2,247 characters) - click Save to apply`
6. Scroll down, click Save Settings
7. Reopen Settings
8. See: `✓ Prompt active (2,247 characters)` ← Success!

### Updating Existing Prompt
1. Open Settings → Context Prompt
2. See: `✓ Prompt active (2,247 characters)`
3. Make changes to the prompt
4. See: `✎ Modified (2,310 characters) - click Save to apply`
5. Scroll down, click Save Settings
6. Reopen Settings
7. See: `✓ Prompt active (2,310 characters)` ← Updated!

### Removing Prompt
1. Open Settings → Context Prompt
2. Delete all text from the box
3. See: `⚠ No prompt configured - using default behavior`
4. Scroll down, click Save Settings
5. AI will use default behavior in new conversations

---

## Technical Details

### Storage Location
Context prompts are saved in:
```
L:\agent\settings.json
```

### Format
```json
{
  "context_prompt": "Your system prompt text here..."
}
```

### How It's Applied
When you start a new conversation, the `chat()` method in `pentest-gui.py` checks for a context prompt and adds it as the first message with role "system":

```python
if context_prompt and not context:
    context.append({"role": "system", "content": context_prompt})
```

This ensures the AI receives your instructions before any user messages.

---

## Best Practices

### ✓ Do This
- Use the recommended prompt from `docs/system-prompt.txt` as a starting point
- Customize it for your specific use case (CTF, red team, bug bounty, learning)
- Check the status indicator before saving
- Test your prompt in a new conversation after saving
- Keep prompts focused and action-oriented

### ✗ Avoid This
- Don't make prompts too long (>5,000 characters gets expensive)
- Don't contradict yourself (e.g., "be brief" then "explain in detail")
- Don't forget to save your changes
- Don't expect it to work in existing conversations (start new one)
- Don't include sensitive information in the prompt

---

## Related Documentation

- [Recommended-System-Prompt.md](Recommended-System-Prompt.md) - Full guide with customization options
- [system-prompt.txt](system-prompt.txt) - Ready-to-use prompt text
- [Context-Prompt-Setup-Guide.md](Context-Prompt-Setup-Guide.md) - Original setup instructions

---

## Changelog

### Version 2 (2026-01-22)
- ✨ Added real-time status indicator
- ✨ Added character count display
- ✨ Added modified/saved state detection
- 📝 Updated description to mention scrolling
- 🎨 Color-coded status (gray/green/orange)

### Version 1 (2026-01-21)
- Initial Context Prompt feature implementation
- Basic text box for entering prompts
- Save to settings.json
- Apply to new conversations

---

*For questions or issues, check the troubleshooting section above or refer to the main documentation.*
