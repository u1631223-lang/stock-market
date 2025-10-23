# Troubleshooting Guide

## Common Issues and Solutions

### 1. LINE Notifications Not Arriving

**Symptoms:**
- GitHub Actions workflow succeeds but no LINE message

**Diagnosis:**
```bash
# Check GitHub Actions logs for LINE notification step
# Look for: "✅ LINE通知送信成功" or "❌ LINE通知送信エラー"
```

**Common Causes:**

a) **Invalid User ID Format**
- Error: `400 Client Error: Bad Request`
- Message: `The property, 'to', in the request body is invalid`
- Solution: User ID must be 33 characters starting with 'U'
- Fix: Update `LINE_TARGET_USER_ID` in GitHub Secrets

b) **Invalid Access Token**
- Error: `401 Unauthorized`
- Solution: Regenerate channel access token in LINE Developers Console
- Fix: Update `LINE_CHANNEL_ACCESS_TOKEN` in GitHub Secrets

c) **User Not Added as Friend**
- Symptom: No error but message doesn't arrive
- Solution: User must add the LINE Official Account as a friend first

### 2. GitHub Actions Permission Errors

**Symptoms:**
- Error: `remote: Permission denied to github-actions[bot]`
- Exit code: 128

**Solution:**
1. Go to repository Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Click Save

### 3. Scraping Skipped During Manual Execution

**Symptoms:**
- Log shows: "現在時刻 XX:XX は取得時間ではありません。処理をスキップします。"

**Explanation:**
- This is INTENTIONAL behavior, not a bug
- Scraping only runs at configured times: 09:15, 09:30, 12:00, 12:45, 14:30 JST

**Solutions:**
a) **Wait for scheduled time** (recommended for production)

b) **Temporary override for testing:**
```python
# In src/scrape_rankings.py, main() function
# Replace:
target = get_current_time_slot()
# With:
target = "morning"  # or "afternoon"

# IMPORTANT: Revert before committing!
```

### 4. HTML Structure Changed

**Symptoms:**
- Error: "ランキングテーブルが見つかりません"
- Empty rankings array in JSON

**Solution:**
1. Open target URL in browser
2. Press F12 to open DevTools
3. Inspect the ranking table structure
4. Update `scrape_ranking()` function in src/scrape_rankings.py:
   - Table selector (class, id, or tag)
   - Row/column extraction logic
5. Test locally before committing

### 5. 403 Forbidden Errors

**Symptoms:**
- HTTP 403 error when accessing Matsui Securities

**Solutions:**
a) **User-Agent Issue**
- Update USER_AGENT in src/config.py
- Use current Chrome/Firefox user agent string

b) **Rate Limiting**
- Check if multiple requests sent too quickly
- Current implementation: 1 request per time slot (should be safe)

c) **IP Blocking**
- GitHub Actions IP may be temporarily blocked
- Wait and retry later
- Consider adding delay or referrer headers

### 6. Execution on Holidays/Weekends

**Symptoms:**
- Workflow triggers but doesn't scrape on weekends/holidays

**Explanation:**
- check_workday.py uses jpholiday for Japanese holiday detection
- Weekends and holidays are intentionally skipped

**Verification:**
```bash
cd src
python check_workday.py
# Shows: "今日は営業日です" or "今日は営業日ではありません"
```

## Testing Workflows

### Test LINE Notifications Only
```bash
# GitHub Actions
Actions → Test Secret Configuration → Run workflow

# Local testing
cd src
export LINE_CHANNEL_ACCESS_TOKEN="..."
export LINE_TARGET_USER_ID="..."
python notify_line.py
```

### Test Full Scraping Flow
```bash
# GitHub Actions (only works during scheduled times)
Actions → Scheduled Ranking Scrape → Run workflow

# Local testing (requires time override)
cd src
python scrape_rankings.py
```

### Verify Environment Variables
```bash
# Check in GitHub Actions logs
# "Check LINE Messaging API secrets exist" step shows:
# ✅ LINE_CHANNEL_ACCESS_TOKEN is set (length: XXX characters)
# ✅ LINE_TARGET_USER_ID is set (length: 33 characters)
```

## Log Analysis

### Successful Scraping
```
[INFO] 松井証券ランキング取得 開始
[INFO] 現在時刻 09:15
[INFO] ランキングデータ取得完了
✅ LINE通知送信成功
```

### Time Slot Mismatch (Expected)
```
[INFO] 現在時刻 16:27 は取得時間ではありません。処理をスキップします。
```

### LINE API Error
```
❌ LINE通知送信エラー: 400 Client Error
   レスポンス: {"message":"..."}
```