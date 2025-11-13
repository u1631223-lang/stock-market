# TradingView Webhook Setup Guide

TradingViewのアラートをLINE通知で受け取るためのセットアップガイドです。

## アーキテクチャ

```
TradingView Alert → Webhook (Vercel) → LINE Messaging API → あなたのLINE
```

## 1. Vercelへのデプロイ

### 前提条件
- Vercelアカウント（無料プラン可）
- Vercel CLIインストール（推奨）

### デプロイ手順

#### オプションA: Vercel CLI（推奨）

```bash
# Vercel CLIインストール（初回のみ）
npm install -g vercel

# プロジェクトルートでデプロイ
cd /path/to/market
vercel

# 初回デプロイ時の質問に回答:
# - Set up and deploy? Yes
# - Which scope? (あなたのアカウント)
# - Link to existing project? No
# - Project name? stock-market (または任意の名前)
# - Directory? ./ (そのままEnter)
# - Override settings? No
```

#### オプションB: GitHub連携（自動デプロイ）

1. [Vercel Dashboard](https://vercel.com/dashboard) にログイン
2. "New Project" → "Import Git Repository"
3. GitHubリポジトリを選択
4. Deploy

### 環境変数の設定

Vercel Dashboardで以下の環境変数を設定：

```
LINE_CHANNEL_ACCESS_TOKEN=（あなたのLINE Channel Access Token）
LINE_TARGET_USER_ID=（あなたのLINE User ID）
TRADINGVIEW_SECRET=（任意の強力なパスワード、例: my_secret_2025_XYZ）
```

設定方法:
1. Vercel Dashboard → プロジェクト選択
2. Settings → Environment Variables
3. 上記3つの変数を追加
4. Save

## 2. Webhook URLの確認

デプロイ完了後、Webhook URLは以下の形式になります：

```
https://your-project-name.vercel.app/api/tradingview
```

例: `https://stock-market-abc123.vercel.app/api/tradingview`

ヘルスチェック（GETリクエスト）:
```bash
curl https://your-project-name.vercel.app/api/tradingview
# → "TradingView Webhook is running"
```

## 3. TradingViewでのアラート設定

### 3.1 アラートの作成

1. TradingViewでチャートを開く
2. アラートアイコン（時計マーク）をクリック
3. "Webhook URL" に上記URLを入力
4. "Message" に以下のJSON形式で入力：

#### パターン1: 基本的なアラート

```json
{
  "ticker": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": "{{close}}",
  "time": "{{timenow}}"
}
```

#### パターン2: カスタムメッセージ

```json
{
  "ticker": "{{ticker}}",
  "message": "{{ticker}} が {{close}} でブレイクアウト！"
}
```

#### パターン3: 詳細情報

```json
{
  "ticker": "{{ticker}}",
  "action": "BUY",
  "strategy": "ゴールデンクロス",
  "price": "{{close}}",
  "volume": "{{volume}}",
  "time": "{{timenow}}",
  "message": "{{ticker}} が買いシグナル発生！価格: {{close}}"
}
```

### 3.2 セキュリティ設定

**重要**: Webhook URL内にシークレットを含める方法もあります：

```
https://your-project-name.vercel.app/api/tradingview?secret=your_secret_here
```

ただし、現在の実装では **HTTPヘッダー** でシークレットを検証しているため、TradingViewの制限により直接ヘッダーを設定できません。

**解決策**:
- URLパラメータでシークレットを渡す実装に変更するか
- Vercel側でIPホワイトリスト制限を追加

## 4. テスト

### ローカルテスト（開発用）

```bash
# Vercel CLIでローカル実行
cd /path/to/market
vercel dev

# 別ターミナルでテストリクエスト送信
curl -X POST http://localhost:3000/api/tradingview \
  -H "Content-Type: application/json" \
  -H "X-TradingView-Secret: your_secret_here" \
  -d '{
    "ticker": "TEST",
    "action": "BUY",
    "price": "12345",
    "time": "2025-11-13 14:00:00"
  }'
```

### 本番テスト

```bash
curl -X POST https://your-project-name.vercel.app/api/tradingview \
  -H "Content-Type: application/json" \
  -H "X-TradingView-Secret: your_secret_here" \
  -d '{
    "ticker": "TEST",
    "message": "テスト通知です"
  }'
```

LINEに通知が届けば成功です。

## 5. TradingViewで使える変数

### 価格関連
- `{{close}}` - 終値
- `{{open}}` - 始値
- `{{high}}` - 高値
- `{{low}}` - 安値
- `{{volume}}` - 出来高

### 銘柄情報
- `{{ticker}}` - ティッカーシンボル（例: AAPL）
- `{{exchange}}` - 取引所

### 時間
- `{{timenow}}` - 現在時刻
- `{{time}}` - バーの時刻

### ストラテジー（Strategyスクリプト使用時）
- `{{strategy.order.action}}` - buy / sell
- `{{strategy.order.contracts}}` - 注文数量
- `{{strategy.position_size}}` - ポジションサイズ

## 6. トラブルシューティング

### 通知が届かない

1. Vercelのログを確認:
```bash
vercel logs your-project-name
```

2. 環境変数が正しく設定されているか確認
3. LINE User IDのフォーマット確認（`U`で始まる33文字）
4. シークレットが一致しているか確認

### 403 Forbidden

- `X-TradingView-Secret` ヘッダーが正しくない
- 環境変数 `TRADINGVIEW_SECRET` の値を確認

### 500 Internal Server Error

- Vercel logsでエラー詳細を確認
- LINE API tokenが無効の可能性

## 7. セキュリティ強化（推奨）

### レート制限の追加

Vercel KV（有料）を使ってレート制限を実装：

```python
from vercel_kv import kv

# 1分間に10リクエストまで
rate_limit = kv.get(f"rate_limit:{ip}")
if rate_limit and int(rate_limit) > 10:
    return 429  # Too Many Requests
```

### IPホワイトリスト

TradingViewのIPアドレスのみ許可（TradingViewがIP公開している場合）

## まとめ

これで、TradingViewのアラートがリアルタイムでLINEに届くようになりました！

**動作確認チェックリスト:**
- ✅ Vercelにデプロイ完了
- ✅ 環境変数設定完了
- ✅ Webhook URLにGETリクエストで応答確認
- ✅ curlでPOSTテスト成功
- ✅ TradingViewでアラート作成
- ✅ LINEに通知到着

問題があれば `vercel logs` を確認してください。
