# Context Prompt Setup & Verification Guide

## Where to Find It in Settings

### Location in Settings Dialog:

The **Context Prompt** section is in Settings, located **between** Font Size and MCP Servers:

```
Settings Dialog (scroll down):
┌─────────────────────────────────────┐
│ Settings                            │
├─────────────────────────────────────┤
│                                     │
│ Session Transcription               │
│ ☑ Enable Transcription              │
│                                     │
│ ─────────────────────────────────  │
│                                     │
│ Font Size                           │
│ [━━━━━━●━━━━━] Current: 14px       │
│                                     │
│ ─────────────────────────────────  │
│                                     │
│ **Context Prompt**          ← HERE │
│ System prompt prepended to all...   │
│ ┌─────────────────────────────┐   │
│ │ [Your prompt goes here]     │   │
│ │                             │   │
│ │ (100px tall textbox)        │   │
│ └─────────────────────────────┘   │
│                                     │
│ ─────────────────────────────────  │
│                                     │
│ OSINT API Keys                      │
│ ...                                 │
│                                     │
│ ─────────────────────────────────  │
│                                     │
│ MCP Servers                         │
│ ...                                 │
│                                     │
│ [Cancel]            [Save Settings] │
└─────────────────────────────────────┘
```

**Note:** You need to **scroll down** in the Settings window to see it!

---

## Step-by-Step Setup

### 1. Open Settings

Click the **⚙️ (gear icon)** in the top-right of the GUI sidebar

### 2. Scroll Down

The Settings dialog is scrollable. **Scroll down** past:
- Session Transcription
- Font Size

### 3. Find "Context Prompt"

You'll see:
```
Context Prompt
System prompt prepended to all conversations

┌─────────────────────────────────────┐
│                                     │
│ [Empty textbox - 100px tall]        │
│                                     │
└─────────────────────────────────────┘
```

### 4. Paste Your Prompt

Copy the system prompt from `L:\docs\system-prompt.txt` and paste it into the textbox.

**Or use this shortened version for testing:**
```
You are a penetration testing assistant. When asked to scan or enumerate, immediately execute the appropriate commands using tool_calls. Explain what each tool does and why you're using it. Focus on practical execution, not just suggestions.
```

### 5. Click "Save Settings"

The button is at the bottom right of the Settings dialog.

### 6. Verify It Saved

1. Close Settings
2. Reopen Settings (⚙️)
3. Scroll down to Context Prompt
4. Your prompt should still be there!

---

## How to Verify It's Working

### Test 1: New Session Behavior

**Without Context Prompt:**
```
User: "Scan 10.10.10.1"
AI: "To scan 10.10.10.1, you can use nmap. Here's a command you could try:
     nmap -sV -sC 10.10.10.1

     This will scan for services and run default scripts."
```

**With Context Prompt:**
```
User: "Scan 10.10.10.1"
AI: "I'll perform a comprehensive scan of 10.10.10.1. Starting with fast port discovery.

     <tool_call>nmap -T4 -p- --min-rate 10000 10.10.10.1</tool_call>

     This discovers all open ports using aggressive timing. Once complete,
     I'll enumerate services on found ports."
```

**Notice:** With the prompt, the AI **immediately executes** instead of just suggesting.

---

### Test 2: Check Session Transcript

After chatting, check the transcript file to see if the system prompt was used:

**Location:** `L:\agent\transcripts\session_YYYYMMDD_HHMMSS.txt`

**Look for at the beginning:**
```
=== Session Started: 2026-01-22 23:45:00 ===

[SYSTEM] You are a penetration testing assistant...
[continues with your prompt]

[USER] Scan 10.10.10.1

[ASSISTANT] I'll perform a comprehensive scan...
```

If you see `[SYSTEM]` with your prompt at the start, it's working!

---

### Test 3: Code-Level Verification

The context prompt is used in two places:

**File:** `pentest-gui.py`

**Line 6262-6264 (chat function):**
```python
context_prompt = self.settings.get("context_prompt", "").strip()
if context_prompt and not context:
    context.append({"role": "system", "content": context_prompt})
```

**Line 6309-6311 (streaming chat):**
```python
context_prompt = self.settings.get("context_prompt", "").strip()
if context_prompt and not context:
    context.append({"role": "system", "content": context_prompt})
```

**What this does:**
- Gets the context_prompt from settings
- If it exists AND the conversation is new (`not context`)
- Adds it as the **first system message** in the conversation

---

### Test 4: Quick Verification Commands

Send these messages and observe the AI's behavior:

**Test Command 1:**
```
"What tools would you use to enumerate a Windows target?"
```

**Expected (with prompt):**
- Lists specific tools (enum4linux, crackmapexec, nmap)
- Provides actual command examples
- Explains what each discovers

**Expected (without prompt):**
- Generic explanation of Windows enumeration
- May not provide specific commands
- More conversational, less action-oriented

---

**Test Command 2:**
```
"Scan 192.168.1.1"
```

**Expected (with prompt):**
- Immediately executes nmap
- Shows `<tool_call>nmap ...</tool_call>`
- Explains flags used

**Expected (without prompt):**
- Suggests using nmap
- May provide example command
- Less likely to auto-execute

---

**Test Command 3:**
```
"Create a task plan to compromise a web server"
```

**Expected (with prompt):**
- Creates structured steps:
  1. Port discovery
  2. Service enumeration
  3. Web directory brute-force
  4. Vulnerability identification
  5. Exploitation attempt
  6. Post-exploitation
- Starts executing step 1

**Expected (without prompt):**
- Provides general methodology
- May not create structured plan
- Likely won't auto-execute

---

## When Does the Prompt Apply?

### ✅ Applied:
- **New conversations** (when you start the GUI or click "New Session")
- **First message** of a conversation
- **After clearing chat**

### ❌ NOT Applied:
- **Mid-conversation** (the system prompt is only added once at the start)
- **Follow-up messages** (context already established)
- **Loaded sessions** (prompt was already in the original context)

**Why?** The code checks `if context_prompt and not context:` - meaning it only adds the prompt if the context list is empty (new conversation).

---

## Troubleshooting

### "I don't see the Context Prompt textbox"

**Solution:** Scroll down in the Settings dialog. It's below Font Size and above MCP Servers.

**Confirm:**
- Settings dialog is 500x700 pixels
- Content is scrollable
- Context Prompt is in the middle section

---

### "I pasted the prompt but it didn't save"

**Checklist:**
1. Did you click "Save Settings" (not Cancel)?
2. Check `L:\agent\settings.json` - should contain:
   ```json
   {
     "context_prompt": "Your prompt text here...",
     ...
   }
   ```
3. Reopen Settings - does the textbox still have your prompt?

---

### "The AI isn't following the prompt"

**Possible Reasons:**

1. **Not a new conversation:**
   - Click "New Session" or restart the GUI
   - The prompt only applies to NEW conversations

2. **Prompt is too long:**
   - The model has a 4096 token context limit
   - Very long prompts may get truncated
   - Try a shorter version (aim for <500 words)

3. **Model limitations:**
   - The htb-pentest model is trained on specific patterns
   - Some behaviors may override the system prompt
   - Try more specific instructions in the prompt

4. **Prompt not saved:**
   - Check settings.json to confirm it's there
   - Look in transcript file for `[SYSTEM]` at start

---

### "How do I know which version is running?"

**Check the welcome message:**

When you start a new session or clear chat, look for:
```
Welcome to HTB Pentest Agent!

Docker Kali: Running - Full Kali toolkit available!

I can help you with:
- Port scanning and enumeration
- Web application testing
...
```

**If your context prompt is working, the welcome message might be different or suppressed** (depending on your prompt's instructions).

---

## Testing Your Prompt

### Quick Test Script:

1. **Set the prompt** in Settings
2. **Click "New Session"** (⊕ button in sidebar)
3. **Send:** "What's your purpose?"

**Expected response (with recommended prompt):**
```
I'm an expert penetration testing assistant trained on Hack The Box
writeups. I help with authorized security testing by:

1. Executing actual commands using 600+ Kali tools
2. Following proper pentesting methodology (recon → enum → exploit)
3. Teaching security concepts while doing practical work

I focus on action-oriented execution, not just suggestions. When you
ask me to scan or enumerate, I'll immediately use tool_calls to run
the appropriate commands.

What would you like me to help you test?
```

**Expected response (without prompt):**
```
Welcome to HTB Pentest Agent! I can help you with penetration testing
tasks like port scanning, web enumeration, SMB testing, and more.
What would you like to do?
```

**Clear difference:** With the prompt, the AI understands its specific role and capabilities.

---

## Recommended Workflow

### Initial Setup:
1. ✅ Open Settings (⚙️)
2. ✅ Scroll to "Context Prompt"
3. ✅ Paste system prompt from `L:\docs\system-prompt.txt`
4. ✅ Save Settings
5. ✅ Click "New Session" (⊕)
6. ✅ Test with "What's your purpose?"

### Daily Use:
- The prompt persists across sessions
- Only applies to NEW conversations
- Click "New Session" when starting a new engagement
- No need to re-paste unless changing the prompt

---

## Advanced: Custom Prompts

### CTF-Focused Prompt (Short Version):
```
You are a CTF-focused penetration testing assistant. When given a
target, immediately execute reconnaissance and enumeration. Look for
common CTF patterns: SQLi, XSS, LFI, SSTI, deserialization. Think
creatively about unusual attack vectors. Execute commands using
tool_calls, don't just suggest.
```

### Bug Bounty Prompt (Short Version):
```
You are a bug bounty hunter assistant. Focus on web application
vulnerabilities and OWASP Top 10. When testing targets, prioritize
high-impact findings. Always execute scans and provide clear PoC
examples. Be methodical and thorough.
```

### Learning Prompt (Short Version):
```
You are a teaching-focused pentesting assistant. Explain every tool,
flag, and technique in detail. Help users understand WHY, not just
HOW. Break complex tasks into learning steps. Execute commands and
explain the output.
```

---

## Visual Confirmation

### When It's Working:

**You'll notice:**
- ✅ AI executes commands immediately
- ✅ Uses `<tool_call>` syntax frequently
- ✅ Explains methodology and tools
- ✅ Creates task plans for complex requests
- ✅ More structured, professional responses

**Transcript shows:**
```
[SYSTEM] You are an expert penetration testing assistant...

[USER] Scan target

[ASSISTANT] I'll perform a comprehensive scan. Starting with...
<tool_call>nmap -T4 -p- --min-rate 10000 target</tool_call>
```

### When It's NOT Working:

**You'll notice:**
- ❌ AI suggests commands instead of running them
- ❌ Less structured responses
- ❌ No task planning
- ❌ More conversational, less action-oriented

**Transcript shows:**
```
[USER] Scan target

[ASSISTANT] To scan the target, you can use nmap...
```

**No `[SYSTEM]` message at the start = prompt not applied**

---

## Summary

### Location:
Settings → Scroll Down → "Context Prompt" section (between Font Size and OSINT API Keys)

### To Use:
1. Paste prompt in textbox
2. Click "Save Settings"
3. Click "New Session"
4. Test with a command

### To Verify:
- AI immediately executes instead of suggesting
- Transcript shows `[SYSTEM]` message at start
- AI follows the behavior/style defined in prompt

### Files:
- Full guide: `L:\docs\Recommended-System-Prompt.md`
- Ready to use: `L:\docs\system-prompt.txt`
- This guide: `L:\docs\Context-Prompt-Setup-Guide.md`

---

*Last Updated: 2026-01-22*
*HTB Pentest Agent v4*
