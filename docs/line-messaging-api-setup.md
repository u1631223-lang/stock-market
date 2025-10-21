# LINE Messaging API セットアップガイド

LINE Notify終了（2025年3月31日）に伴い、LINE Messaging APIへ移行しました。

## 目次

1. [LINE公式アカウントの作成](#line公式アカウントの作成)
2. [Messaging APIチャネルの作成](#messaging-apiチャネルの作成)
3. [Channel Access Tokenの取得](#channel-access-tokenの取得)
4. [ユーザーIDの取得](#ユーザーidの取得)
5. [GitHub Secretsへの登録](#github-secretsへの登録)
6. [動作確認](#動作確認)

---

## LINE公式アカウントの作成

### Step 1: LINE Developersコンソールにアクセス

1. ブラウザで https://developers.line.biz/console/ を開く
2. 右上の **「ログイン」** をクリック
3. LINEアカウントでログイン（メールアドレス＆パスワード、またはQRコード）

### Step 2: プロバイダーを作成（初回のみ）

1. ログイン後、**「Create a new provider」**（新規プロバイダー作成）をクリック
2. プロバイダー名を入力：
   ```
   例: 個人開発
   ```
   - 任意の名前でOK（後で変更可能）
3. **「Create」** をクリック

### Step 3: チャネルを作成

1. 作成したプロバイダーをクリック
2. **「Create a new channel」** をクリック
3. チャネルタイプで **「Messaging API」** を選択

### Step 4: チャネル情報を入力

以下の項目を入力します：

| 項目 | 入力内容 | 説明 |
|------|----------|------|
| **Channel name** | `松井証券ランキング通知` | 公式アカウント名（任意） |
| **Channel description** | `株式ランキング自動取得システムの通知用` | 説明（任意） |
| **Category** | `Personal` または `Finance` | カテゴリを選択 |
| **Subcategory** | 適切なものを選択 | サブカテゴリ |
| **Email address** | あなたのメールアドレス | 連絡先 |

プライバシーポリシーと利用規約は個人利用の場合は任意（空欄でOK）

### Step 5: 規約に同意して作成

1. 下部の規約チェックボックスにチェック
   - ☑ LINE Official Account Terms of Use
   - ☑ LINE Official Account API Terms of Use
2. **「Create」** をクリック

---

## Messaging APIチャネルの作成

チャネル作成後、自動的にチャネル設定画面に遷移します。

### 重要な設定項目

#### 1. Webhook設定（オフのままでOK）

- **Use webhook**: オフ
  - 今回は通知送信のみなので、Webhookは不要

#### 2. 応答設定

1. チャネル設定画面の **「Messaging API」** タブをクリック
2. 下にスクロールして **「LINE Official Account features」** セクションを確認
3. 以下のように設定：

| 項目 | 設定値 | 理由 |
|------|--------|------|
| **Auto-reply messages** | オフ | 自動応答不要 |
| **Greeting messages** | オフ | 挨拶メッセージ不要 |
| **Allow bot to join group chats** | 任意 | 個人利用なので不要 |

---

## Channel Access Tokenの取得

### Step 1: Channel Access Tokenを発行

1. チャネル設定画面の **「Messaging API」** タブを開く
2. 下にスクロールして **「Channel access token (long-lived)」** セクションを見つける
3. **「Issue」** ボタンをクリック

### Step 2: トークンをコピー

1. 発行されたトークン（約170文字の長い文字列）が表示されます
   ```
   例: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...（以下省略）
   ```
2. 右側の **「Copy」** ボタンをクリックしてコピー
3. **必ずメモ帳などに保存してください**（後で使用）

⚠️ **セキュリティ注意事項:**
- このトークンは絶対に他人に教えないでください
- GitHubのコードに直接書かないでください（GitHub Secretsを使用）
- 漏洩した場合は、すぐにトークンを再発行してください

---

## ユーザーIDの取得

通知を受け取るためには、あなた自身のLINE User IDが必要です。

### 方法1: 公式アカウントを友だち追加してIDを確認（簡単）

#### Step 1: QRコードで友だち追加

1. チャネル設定画面の **「Messaging API」** タブを開く
2. **「QR code」** をクリックしてQRコードを表示
3. スマートフォンのLINEアプリで読み取り
4. **「追加」** をタップして友だち登録

#### Step 2: ユーザーIDを取得（Webhookを一時的に使用）

この方法は少し技術的です。以下の簡易的な方法を推奨します：

**簡易方法: テストメッセージでIDを取得**

1. 一時的に以下のPythonスクリプトを実行してIDを取得します

以下のスクリプトを `get_user_id.py` として保存：

```python
#!/usr/bin/env python3
"""
LINE Messaging APIでUser IDを取得するスクリプト
友だち追加した公式アカウントにメッセージを送信後、このスクリプトを実行
"""
import os
import sys

# Channel Access Tokenを環境変数から取得
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

if not CHANNEL_ACCESS_TOKEN:
    print("エラー: LINE_CHANNEL_ACCESS_TOKEN 環境変数が設定されていません")
    print("以下のコマンドで設定してください:")
    print('export LINE_CHANNEL_ACCESS_TOKEN="your_token_here"')
    sys.exit(1)

# Webhookを使わずにUser IDを取得する方法の説明
print("""
============================================================
LINE User ID 取得方法
============================================================

残念ながら、Messaging APIではWebhookなしでUser IDを直接取得できません。
以下の2つの方法があります:

【方法A: LINE Official Account Managerで確認（推奨）】

1. https://manager.line.biz/ にアクセス
2. 作成した公式アカウントを選択
3. 左メニューから「チャット」を選択
4. 友だちからメッセージが届いている場合、ユーザー名をクリック
5. プロフィール画面に「User ID」が表示されます
   例: U1234567890abcdef1234567890abcdef

【方法B: Webhookを一時的に有効化（上級者向け）】

1. ngrokなどでローカルWebhookサーバーを立てる
2. LINE DevelopersコンソールでWebhook URLを設定
3. 公式アカウントにメッセージを送信
4. Webhookイベントから userId を取得

============================================================

取得したUser IDは以下のように保存してください:
export LINE_USER_ID="U1234567890abcdef1234567890abcdef"
============================================================
""")
```

#### Step 3: LINE Official Account Managerで確認（最も簡単）

1. https://manager.line.biz/ にアクセス
2. 作成した公式アカウントを選択
3. 左メニューから **「ホーム」** → **「アカウント設定」** を選択
4. **「基本設定」** タブで **「あなたのユーザーID」** をコピー

または:

1. https://manager.line.biz/ にアクセス
2. 作成した公式アカウントを選択
3. 左メニューから **「チャット」** を選択
4. スマホから公式アカウントに「テスト」とメッセージを送信
5. チャット画面にメッセージが表示されたら、ユーザー名をクリック
6. 表示されるプロフィールに **User ID** が記載されています
   ```
   例: U1234567890abcdef1234567890abcdef
   ```
7. このIDをコピーして保存

---

## GitHub Secretsへの登録

### 必要なSecret（2つ）

| Secret名 | 値 | 取得場所 |
|----------|-----|----------|
| `LINE_CHANNEL_ACCESS_TOKEN` | 約170文字のトークン | LINE Developers コンソール |
| `LINE_USER_ID` | `U` で始まる33文字のID | LINE Official Account Manager |

### 設定手順

#### Secret 1: LINE_CHANNEL_ACCESS_TOKEN

1. GitHubリポジトリを開く
2. **Settings** → **Secrets and variables** → **Actions**
3. **「New repository secret」** をクリック
4. **Name**: `LINE_CHANNEL_ACCESS_TOKEN`
5. **Secret**: 先ほどコピーしたChannel Access Tokenを貼り付け
6. **「Add secret」** をクリック

#### Secret 2: LINE_USER_ID

1. 同じページで **「New repository secret」** をクリック
2. **Name**: `LINE_USER_ID`
3. **Secret**: 取得したUser IDを貼り付け（`U`で始まる文字列）
4. **「Add secret」** をクリック

### 設定完了の確認

Secretsページに以下の2つが表示されればOK:

```
Repository secrets

LINE_CHANNEL_ACCESS_TOKEN    Updated X seconds ago    [Update] [Remove]
LINE_USER_ID                 Updated X seconds ago    [Update] [Remove]
```

---

## 動作確認

### ローカルでのテスト

```bash
# 環境変数を設定
export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"
export LINE_USER_ID="your_user_id"

# 仮想環境を有効化
source venv/bin/activate

# テストスクリプト実行
cd src
python notify_line.py
```

正常に動作すれば、LINEアプリに通知が届きます。

### GitHub Actionsでのテスト

1. GitHubリポジトリの **Actions** タブを開く
2. **「Test Secret Configuration」** ワークフローを選択
3. **「Run workflow」** をクリック
4. 実行完了後、LINEに通知が届くことを確認

---

## トラブルシューティング

### エラー: 401 Unauthorized

- Channel Access Tokenが間違っている可能性
- トークンを再発行して、GitHub Secretsを更新

### エラー: 400 Bad Request

- User IDが間違っている可能性
- User IDは `U` で始まる33文字の文字列か確認

### 通知が届かない

1. 公式アカウントを友だち追加しているか確認
2. LINEアプリの通知設定を確認
3. ブロックしていないか確認

### User IDが取得できない

- LINE Official Account Manager（https://manager.line.biz/）の「チャット」機能を使用
- 公式アカウントにメッセージを送信後、プロフィールから確認

---

## 参考リンク

- [LINE Messaging API ドキュメント](https://developers.line.biz/ja/docs/messaging-api/)
- [LINE Developers Console](https://developers.line.biz/console/)
- [LINE Official Account Manager](https://manager.line.biz/)
