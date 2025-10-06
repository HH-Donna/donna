# Edge Cases and Troubleshooting Guide

## Overview

This document outlines potential edge cases, common issues, and troubleshooting steps for the Donna ElevenLabs Agent CLI integration.

---

## 🔐 Authentication & API Issues

### Edge Case 1: API Key Expiration or Invalidity

**Symptoms:**
- `401 Unauthorized` errors
- "Invalid API key" messages
- Sync/fetch commands fail silently

**Solutions:**
1. **Verify API Key is Valid:**
   ```bash
   cd /Users/voyager/Documents/GitHub/donna/agent
   export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
   agents whoami
   ```

2. **Regenerate API Key:**
   - Visit: https://elevenlabs.io/app/settings/api-keys
   - Generate new API key
   - Update `.env` file
   - Re-export: `export ELEVENLABS_API_KEY="your-new-key"`

3. **Check for Trailing Spaces:**
   ```bash
   # Trim any whitespace
   export ELEVENLABS_API_KEY=$(echo "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a" | xargs)
   ```

### Edge Case 2: Rate Limiting

**Symptoms:**
- `429 Too Many Requests` errors
- Sync commands hang or timeout
- Intermittent failures

**Solutions:**
1. **Implement Retry Logic:**
   ```bash
   # Retry sync with backoff
   for i in {1..3}; do
     agents sync --env dev && break || sleep 5
   done
   ```

2. **Check Rate Limits:**
   - Review your plan limits at https://elevenlabs.io/app/settings/billing
   - Upgrade plan if hitting limits frequently
   - Space out sync operations (use `agents watch` for continuous sync)

### Edge Case 3: Network/Proxy Issues

**Symptoms:**
- Connection timeouts
- SSL/TLS errors
- "ENOTFOUND" or "ECONNREFUSED" errors

**Solutions:**
1. **Check Network Connectivity:**
   ```bash
   curl -I https://api.elevenlabs.io/v1/agents
   ```

2. **Configure Proxy (if needed):**
   ```bash
   export HTTP_PROXY="http://your-proxy:port"
   export HTTPS_PROXY="http://your-proxy:port"
   ```

3. **Disable SSL Verification (last resort, not recommended for prod):**
   ```bash
   export NODE_TLS_REJECT_UNAUTHORIZED=0
   ```

---

## 📁 Configuration & File Issues

### Edge Case 4: Invalid JSON Configuration

**Symptoms:**
- "Unexpected token" errors
- Sync fails with parsing errors
- CLI commands hang

**Solutions:**
1. **Validate JSON Syntax:**
   ```bash
   # Check dev config
   jq . agent_configs/dev/donna-billing-verifier.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
   
   # Check prod config
   jq . agent_configs/prod/donna-billing-verifier.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
   ```

2. **Pretty-print and Fix:**
   ```bash
   # Auto-format JSON
   jq . agent_configs/dev/donna-billing-verifier.json > temp.json && mv temp.json agent_configs/dev/donna-billing-verifier.json
   ```

3. **Re-fetch from Dashboard:**
   ```bash
   # Backup current config
   cp agent_configs/dev/donna-billing-verifier.json agent_configs/dev/donna-billing-verifier.json.backup
   
   # Re-fetch fresh config
   agents fetch
   ```

### Edge Case 5: agents.json/agents.lock Mismatch

**Symptoms:**
- "Agent not found" errors
- Duplicate agents showing in status
- Wrong environment being deployed

**Solutions:**
1. **Verify Structure:**
   ```bash
   # Check agents.json structure
   cat agents.json | jq .
   
   # Check agents.lock structure
   cat agents.lock | jq .
   ```

2. **Regenerate agents.lock:**
   ```bash
   # Backup
   cp agents.lock agents.lock.backup
   
   # Sync will regenerate lock file
   agents sync --env dev
   ```

3. **Manual Fix (if needed):**
   - Ensure `agents.json` has correct `name` and `config` paths
   - Ensure `agents.lock` has correct agent IDs and hashes
   - Both should reference the same agent names

### Edge Case 6: Missing or Incorrect Agent ID

**Symptoms:**
- "Agent not found on platform"
- Creating new agents instead of updating existing ones
- `agents.lock` shows different IDs

**Solutions:**
1. **Verify Agent ID:**
   ```bash
   # Check what's in agents.lock
   cat agents.lock | jq '.agents'
   
   # Should show: agent_2601k6rm4bjae2z9amfm5w1y6aps
   ```

2. **List All Agents on Platform:**
   - Visit: https://elevenlabs.io/app/conversational-ai
   - Find your agent
   - Copy the ID from the URL: `/app/conversational-ai/agents/[AGENT_ID]`

3. **Update Manually:**
   ```bash
   # If wrong agent ID, update agents.lock
   nano agents.lock
   # Update the "id" field under agents > Donna > prod
   ```

---

## 🚀 Deployment Issues

### Edge Case 7: Sync Fails with "paths[0] undefined"

**Symptoms:**
- Error message: "paths[0] undefined"
- Sync command fails
- Status command shows the error

**Solutions:**
1. **This is a Known CLI Bug** - Your configs are likely fine
2. **Workaround 1: Manual Upload**
   - Go to https://elevenlabs.io/app/conversational-ai
   - Open your agent
   - Copy/paste configuration JSON manually
   - Use "Import JSON" feature if available

3. **Workaround 2: Use Different CLI Version**
   ```bash
   # Check current version
   agents --version
   
   # Try updating CLI
   npm update -g @elevenlabs/agents-cli
   
   # Or install specific version
   npm install -g @elevenlabs/agents-cli@0.4.0
   ```

4. **Workaround 3: Check File Paths**
   ```bash
   # Ensure paths in agents.json are relative and correct
   ls -la agent_configs/dev/donna-billing-verifier.json
   ls -la agent_configs/prod/donna-billing-verifier.json
   ```

### Edge Case 8: Deploying to Wrong Environment

**Symptoms:**
- Production changes appear in dev
- Dev settings override prod
- Tags/privacy settings mixed up

**Solutions:**
1. **Always Specify Environment:**
   ```bash
   # DO THIS:
   agents sync --env dev
   agents sync --env prod
   
   # NOT THIS:
   agents sync  # May use wrong default
   ```

2. **Use Dry-Run First:**
   ```bash
   # Preview changes before deploying
   agents sync --env dev --dry-run
   agents sync --env prod --dry-run
   ```

3. **Verify After Deployment:**
   ```bash
   # Check agent status
   agents status
   
   # Verify in dashboard
   # Visit: https://elevenlabs.io/app/conversational-ai
   ```

### Edge Case 9: Configuration Changes Not Appearing

**Symptoms:**
- Made changes to JSON but not reflected in dashboard
- Old configuration still active
- Sync succeeds but changes don't apply

**Solutions:**
1. **Check Hash in agents.lock:**
   ```bash
   # The hash should change when config changes
   cat agents.lock | jq '.agents.Donna.prod.hash'
   ```

2. **Force Re-sync:**
   ```bash
   # Update agents.lock hash manually to force update
   # Or delete the agent from lock and re-sync
   ```

3. **Clear Cache (if applicable):**
   ```bash
   # CLI may cache configs
   rm -rf ~/.elevenlabs/cache  # If this directory exists
   ```

---

## 🧪 Testing & Development Issues

### Edge Case 10: Dev and Prod Configs Diverge

**Symptoms:**
- Dev behaves differently than prod
- Unexpected behavior in production
- Different voices/models between environments

**Solutions:**
1. **Track Differences Intentionally:**
   ```bash
   # Compare configs
   diff agent_configs/dev/donna-billing-verifier.json agent_configs/prod/donna-billing-verifier.json
   ```

2. **Document Intended Differences:**
   - Dev: `record_voice: false`, `tags: ["environment:dev"]`
   - Prod: `record_voice: true`, `tags: ["environment:prod"]`

3. **Sync Dev to Prod (when ready):**
   ```bash
   # Copy dev to prod (with privacy adjustments)
   cp agent_configs/dev/donna-billing-verifier.json agent_configs/prod/donna-billing-verifier.json
   
   # Update prod-specific settings
   # - Change tags
   # - Enable voice recording
   # - Adjust retention policies
   ```

### Edge Case 11: Tool Configuration Missing or Outdated

**Symptoms:**
- Agent can't use expected tools
- "Tool not found" errors in conversations
- Tool IDs mismatch

**Solutions:**
1. **Verify Tool IDs in Config:**
   ```bash
   # Check tool_ids in agent config
   cat agent_configs/prod/donna-billing-verifier.json | jq '.conversation_config.agent.prompt.tool_ids'
   
   # Should include: tool_3901k6sdzymwef1bk1k2bwfenkdm
   ```

2. **Fetch Latest Tools:**
   ```bash
   # Re-fetch agent to get updated tool IDs
   agents fetch
   ```

3. **Add Tools Manually:**
   - Visit dashboard: https://elevenlabs.io/app/conversational-ai
   - Open agent > Tools
   - Verify all tools are attached
   - Update JSON if needed

### Edge Case 12: Dynamic Variables Not Working

**Symptoms:**
- Placeholders like `{{customer_org}}` not replaced
- Agent says literal "customer_org" in conversation
- Variables undefined or null

**Solutions:**
1. **Verify Dynamic Variable Configuration:**
   ```bash
   # Check dynamic_variables section
   cat agent_configs/prod/donna-billing-verifier.json | jq '.conversation_config.agent.dynamic_variables'
   ```

2. **Ensure Variables are Passed at Runtime:**
   ```python
   # When initiating conversation via API
   conversation = client.conversational_ai.start_conversation(
       agent_id="agent_2601k6rm4bjae2z9amfm5w1y6aps",
       variables={
           "customer_org": "Pixamp, Inc",
           "vendor__legal_name": "Amazon Web Services"
       }
   )
   ```

3. **Set Default Placeholders:**
   - Update `dynamic_variable_placeholders` in agent config
   - Provide sensible defaults for testing

---

## 🔄 CI/CD & Automation Issues

### Edge Case 13: GitHub Actions Deployment Fails

**Symptoms:**
- CI/CD pipeline fails at agent sync step
- Authentication errors in GitHub Actions
- Workflow doesn't trigger on agent config changes

**Solutions:**
1. **Set GitHub Secrets:**
   - Go to repo settings > Secrets and variables > Actions
   - Add secret: `ELEVENLABS_API_KEY`
   - Value: `sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a`

2. **Update Workflow Path Triggers:**
   ```yaml
   on:
     push:
       branches: [main, cli-agent-integration]
       paths:
         - 'agent/**'
         - 'agent/agent_configs/**'
   ```

3. **Add Verbose Logging:**
   ```yaml
   - name: Deploy Agent
     run: |
       cd agent
       agents whoami  # Verify auth
       agents status  # Check status
       agents sync --env prod
   ```

### Edge Case 14: Watch Mode Causing Infinite Loops

**Symptoms:**
- `agents watch` keeps syncing repeatedly
- File changes trigger multiple syncs
- CPU usage spikes

**Solutions:**
1. **Ignore Temporary Files:**
   ```bash
   # Create .agentsignore file
   echo "*.backup" > .agentsignore
   echo "*.tmp" >> .agentsignore
   echo ".env" >> .agentsignore
   ```

2. **Use Specific File Watching:**
   ```bash
   # Watch only specific config files
   # (Check CLI docs for this feature)
   ```

3. **Use Manual Sync Instead:**
   ```bash
   # For development, sync manually after changes
   agents sync --env dev
   ```

---

## 🔧 Platform-Specific Issues

### Edge Case 15: Agent Works in Dashboard but Not via API

**Symptoms:**
- Agent responds correctly when testing in dashboard
- API calls fail or get no response
- Different behavior between widget and API

**Solutions:**
1. **Check API Authentication:**
   ```bash
   curl -X POST https://api.elevenlabs.io/v1/convai/conversations \
     -H "xi-api-key: sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "agent_2601k6rm4bjae2z9amfm5w1y6aps"
     }'
   ```

2. **Verify Agent is Published:**
   - Dashboard > Agent > Settings
   - Ensure "Published" toggle is ON
   - Check access permissions

3. **Review Platform Settings:**
   - Check `platform_settings.auth.enable_auth`
   - If enabled, you need allowlist or proper auth tokens

### Edge Case 16: Voice Model Changes Not Applying

**Symptoms:**
- Changed `voice_id` but still hear old voice
- TTS settings don't update
- Audio quality remains the same

**Solutions:**
1. **Check Override Settings:**
   ```bash
   # Look for overrides section
   cat agent_configs/prod/donna-billing-verifier.json | jq '.platform_settings.overrides'
   ```

2. **Verify Voice ID is Valid:**
   - Visit: https://elevenlabs.io/app/voice-library
   - Check that voice ID exists: `EXAVITQu4vr4xnSDxMaL`
   - Try a different voice ID to test

3. **Clear Conversation Cache:**
   - End all active conversations
   - Start a fresh conversation to test
   - May take a few minutes for changes to propagate

---

## 📊 Monitoring & Debugging

### Edge Case 17: Can't Access Conversation Transcripts

**Symptoms:**
- No transcripts appearing in dashboard
- `data_collection` fields empty
- Can't debug conversation issues

**Solutions:**
1. **Enable Transcript Recording:**
   ```json
   "privacy": {
     "record_voice": true,
     "retention_days": 30,
     "delete_transcript_and_pii": false
   }
   ```

2. **Check Widget Settings:**
   ```json
   "widget": {
     "transcript_enabled": true
   }
   ```

3. **Verify Data Collection Fields:**
   - Ensure `data_collection` section has required fields
   - Check that LLM is extracting data correctly

### Edge Case 18: Evaluation Criteria Not Working

**Symptoms:**
- Conversations not being scored
- Evaluation results empty
- Criteria not appearing in dashboard

**Solutions:**
1. **Verify Criteria Configuration:**
   ```bash
   cat agent_configs/prod/donna-billing-verifier.json | jq '.platform_settings.evaluation.criteria'
   ```

2. **Check if Conversations are Complete:**
   - Evaluations run after conversation ends
   - May take a few minutes to process
   - Check "Conversations" tab in dashboard

3. **Re-run Evaluations:**
   - Dashboard > Agent > Evaluations
   - Select conversations to re-evaluate

---

## 🛡️ Security Considerations

### Edge Case 19: API Keys Exposed in Logs or Git

**Symptoms:**
- API key appears in command history
- Key committed to Git repository
- Keys visible in CI/CD logs

**Solutions:**
1. **Immediate Mitigation:**
   ```bash
   # Revoke the exposed key immediately
   # Visit: https://elevenlabs.io/app/settings/api-keys
   # Delete the old key
   # Generate a new one
   ```

2. **Clean Git History (if committed):**
   ```bash
   # Remove sensitive file from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch agent/.env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

3. **Prevent Future Exposure:**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.key" >> .gitignore
   echo "agents.lock" >> .gitignore  # Contains hashes, not secrets
   
   # Use secret management
   # Store in environment variables
   # Use GitHub Secrets for CI/CD
   ```

### Edge Case 20: Unauthorized Access to Agent

**Symptoms:**
- Unexpected conversations in dashboard
- Usage quota consumed unexpectedly
- Agent behavior changed without your knowledge

**Solutions:**
1. **Enable Auth Protection:**
   ```json
   "platform_settings": {
     "auth": {
       "enable_auth": true,
       "allowlist": ["your-domain.com"]
     }
   }
   ```

2. **Rotate API Keys:**
   ```bash
   # Generate new API key
   # Update .env file
   # Update CI/CD secrets
   # Revoke old key
   ```

3. **Monitor Usage:**
   - Dashboard > Settings > Usage
   - Set up usage alerts
   - Review conversation logs regularly

---

## 🔄 Recovery Procedures

### Complete Reset Procedure

If everything is broken and you need to start fresh:

```bash
# 1. Backup current state
cd /Users/voyager/Documents/GitHub/donna/agent
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz agent_configs/ agents.json agents.lock

# 2. Clean up
rm -rf agent_configs/dev/* agent_configs/prod/*
cp agents.lock agents.lock.backup

# 3. Re-fetch from platform
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
agents fetch

# 4. Reorganize configs
mv agent_configs/donna.json agent_configs/prod/donna-billing-verifier.json
cp agent_configs/prod/donna-billing-verifier.json agent_configs/dev/donna-billing-verifier.json

# 5. Update dev config for testing
# - Change tags to ["environment:dev"]
# - Disable voice recording
# - Set retention_days to 7

# 6. Verify and sync
agents status
agents sync --env dev --dry-run
agents sync --env dev
```

---

## 📞 Support Resources

### When to Reach Out for Help

1. **CLI Issues:** https://github.com/elevenlabs/elevenlabs-agents-cli/issues
2. **API Issues:** support@elevenlabs.io
3. **Platform Issues:** https://elevenlabs.io/app/support
4. **Documentation:** https://elevenlabs.io/docs/agents-platform

### Diagnostic Information to Provide

When reporting issues, include:

```bash
# System info
uname -a
node --version
npm --version
agents --version

# Configuration info (redact sensitive data)
cat agents.json
cat agents.lock

# Error logs
# Copy the full error message and stack trace
```

---

## ✅ Best Practices to Avoid Edge Cases

1. **Always Use Version Control:**
   - Commit agent configs to Git
   - Use branches for major changes
   - Tag releases for production deployments

2. **Test in Dev First:**
   - Never deploy directly to prod
   - Use `--dry-run` flag
   - Test with sample conversations

3. **Environment Variables:**
   - Never hardcode API keys
   - Use `.env` files (gitignored)
   - Use secret managers in production

4. **Regular Backups:**
   ```bash
   # Create backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d-%H%M%S)
   tar -czf backups/agent-backup-$DATE.tar.gz agent_configs/ agents.json agents.lock
   ```

5. **Monitor and Alert:**
   - Set up usage alerts
   - Review conversation logs weekly
   - Track evaluation metrics

6. **Documentation:**
   - Document any configuration changes
   - Keep this edge case guide updated
   - Share knowledge with team

---

## 🎯 Quick Reference

### Most Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Auth error | `agents whoami` → re-login if needed |
| Config not syncing | `agents sync --env [env] --dry-run` |
| Wrong environment | Always specify `--env dev` or `--env prod` |
| JSON invalid | `jq . config.json` to validate |
| Agent not found | Check agent ID in `agents.lock` |

### Emergency Commands

```bash
# Check auth
agents whoami

# Validate JSON
jq . agent_configs/prod/donna-billing-verifier.json

# Preview sync
agents sync --env prod --dry-run

# Force re-fetch
rm agents.lock && agents fetch

# Complete status
agents status
```

---

**Last Updated:** 2025-10-05  
**Agent ID:** agent_2601k6rm4bjae2z9amfm5w1y6aps  
**CLI Version:** 0.4.2
