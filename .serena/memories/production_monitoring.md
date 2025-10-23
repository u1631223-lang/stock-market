# 本番運用モニタリング

## 現在のステータス

**最終更新:** 2025-10-22 15:00  
**本番運用開始日:** 2025-10-21  
**稼働状況:** 🟡 修正適用済み、動作確認待ち

## 実行スケジュール（JST）

| 時刻 | 対象 | UTC時刻 | ステータス |
|-----|------|---------|----------|
| 09:15 | morning | 00:15 | ⏳ 明日確認予定 |
| 09:30 | morning | 00:30 | ⏳ 明日確認予定 |
| 12:00 | morning | 03:00 | ⏳ 明日確認予定 |
| 12:45 | afternoon | 03:45 | ⏳ 明日確認予定 |
| 14:30 | afternoon | 05:30 | ⏳ 今日確認予定 |

## 問題履歴

### Issue #1: LINE通知が届かない（2025-10-22）

**症状:**
- 本番運用開始後、スケジュール実行時刻になってもLINE通知が届かない

**調査:**
- GitHub Actionsは正常に実行されていることを確認
- 実行ログから、時刻判定でスキップされていることを発見
- 原因: GitHub Actions cronの遅延により、完全一致判定が失敗

**修正:**
- `get_current_time_slot()`を±15分の範囲判定に変更
- コミット: 6c059cd
- 修正適用日時: 2025-10-22 15:00

**確認予定:**
- 2025-10-23 朝（09:15頃）に動作確認
- または本日14:30頃の実行で確認

**ステータス:** 🟡 修正済み・確認待ち

## 次回確認チェックリスト

### 2025-10-23（明日）朝の確認

- [ ] GitHub Actions実行履歴を確認（09:15頃）
  - URL: https://github.com/u1631223-lang/stock-market/actions
  
- [ ] 実行ログを確認
  - [ ] "Run scraper"ステップで処理が実行されたか
  - [ ] "現在時刻 XX:XX は YY:YY の実行時間帯です（許容範囲: ±15分）" のログがあるか
  - [ ] エラーなく完了しているか
  
- [ ] データコミットを確認
  - [ ] `data/morning/ranking_20251023_HHMM.json` が作成されているか
  - [ ] gitコミット履歴に追加されているか
  
- [ ] LINE通知を確認
  - [ ] Messaging APIから通知が届いているか
  - [ ] 通知内容に正しいランキングデータ（Top 10）が含まれているか
  
- [ ] 全時間帯の確認（1日を通して）
  - [ ] 09:15 実行成功
  - [ ] 09:30 実行成功
  - [ ] 12:00 実行成功
  - [ ] 12:45 実行成功
  - [ ] 14:30 実行成功

## モニタリング方法

### 1. GitHub Actions実行履歴の確認

```
https://github.com/u1631223-lang/stock-market/actions
```

- 緑チェック（✅）: 成功
- 赤バツ（❌）: 失敗
- 実行時刻が±15分の範囲内に収まっているか確認

### 2. 実行ログの確認

各実行をクリックして、以下を確認：

- **Run scraper** ステップ:
  ```
  [INFO] 現在時刻 XX:XX は YY:YY の実行時間帯です（許容範囲: ±15分）
  [INFO] ランキング取得成功
  ```

- **Commit and push data** ステップ:
  ```
  [main xxxxxxx] Add ranking data: YYYY-MM-DD HH:MM
  ```

### 3. データファイルの確認

リポジトリのdata/ディレクトリを確認：

```
https://github.com/u1631223-lang/stock-market/tree/main/data
```

- `data/morning/ranking_YYYYMMDD_HHMM.json`
- `data/afternoon/ranking_YYYYMMDD_HHMM.json`

### 4. LINE通知の確認

LINE Messaging APIボットからの通知を確認：

期待される通知フォーマット:
```
📊 松井証券ランキング取得完了

🕐 取得日時: 2025-10-23 09:XX
📌 対象: morning（朝ランキング）

🏆 Top 10:
1位: [銘柄コード] 銘柄名
2位: [銘柄コード] 銘柄名
...
10位: [銘柄コード] 銘柄名
```

## トラブルシューティング

### 通知が届かない場合

1. **GitHub Actions実行履歴を確認**
   - 実行されているか？
   - 成功しているか？
   - ログにエラーはないか？

2. **Secretsの確認**
   ```
   https://github.com/u1631223-lang/stock-market/settings/secrets/actions
   ```
   - `LINE_CHANNEL_ACCESS_TOKEN` 設定済みか
   - `LINE_TARGET_USER_ID` 設定済みか

3. **手動実行テスト**
   ```
   https://github.com/u1631223-lang/stock-market/actions/workflows/scrape_rankings.yml
   ```
   - "Run workflow"ボタンで手動実行
   - 結果とログを確認

4. **ローカルテスト**
   ```bash
   cd /Users/u1/dev/market
   source venv/bin/activate
   cd src
   python scrape_rankings.py
   ```

### データがコミットされない場合

1. **Workflow権限の確認**
   ```
   https://github.com/u1631223-lang/stock-market/settings/actions
   ```
   - "Read and write permissions"が選択されているか

2. **gitコミットログの確認**
   - "Commit and push data"ステップのログを見る
   - "nothing to commit"メッセージがあるか
   - エラーメッセージがあるか

### スクレイピングが失敗する場合

1. **403エラー**
   - User-Agentが正しく設定されているか
   - 松井証券がanti-scraping対策を強化した可能性

2. **HTMLパースエラー**
   - サイトのHTML構造が変更された可能性
   - `scrape_ranking()`関数のセレクタを更新する必要あり

3. **タイムアウト**
   - ネットワーク遅延
   - REQUEST_TIMEOUTを調整

## 期待される正常動作

### 1日の実行フロー

```
00:15 UTC (09:15 JST) → morning ランキング取得 → LINE通知
00:30 UTC (09:30 JST) → morning ランキング取得 → LINE通知
03:00 UTC (12:00 JST) → morning ランキング取得 → LINE通知
03:45 UTC (12:45 JST) → afternoon ランキング取得 → LINE通知
05:30 UTC (14:30 JST) → afternoon ランキング取得 → LINE通知
```

### 正常な実行ログの例

```
[2025-10-23 09:17:32] [INFO] ========================================
[2025-10-23 09:17:32] [INFO] 松井証券ランキング取得 開始
[2025-10-23 09:17:32] [INFO] 現在時刻 09:17 は 09:15 の実行時間帯です（許容範囲: ±15分）
[2025-10-23 09:17:33] [INFO] ランキング取得成功: 10件
[2025-10-23 09:17:33] [INFO] JSONファイルを保存しました: /path/to/data/morning/ranking_20251023_0917.json
[2025-10-23 09:17:34] [INFO] LINE通知を送信しました
[2025-10-23 09:17:34] [INFO] 松井証券ランキング取得 完了
[2025-10-23 09:17:34] [INFO] ========================================
```

## 成功基準

次回確認（2025-10-23）で以下がすべて満たされれば、本番運用は正常稼働と判断：

- [ ] 5つのスケジュール実行すべてが成功
- [ ] 各実行でJSONファイルが正しく保存
- [ ] 各実行でgitコミットが自動実行
- [ ] 各実行でLINE通知が送信
- [ ] エラーログが出ていない
- [ ] スクレイピングデータが正しい（Top 10件取得）

## 関連リソース

- **GitHubリポジトリ:** https://github.com/u1631223-lang/stock-market
- **GitHub Actions:** https://github.com/u1631223-lang/stock-market/actions
- **ワークフロー設定:** `.github/workflows/scrape_rankings.yml`
- **スクレイピングスクリプト:** `src/scrape_rankings.py`
- **設定ファイル:** `src/config.py`
- **修正履歴:** `fix_history.md` メモリ参照
