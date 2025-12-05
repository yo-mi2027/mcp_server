# mcp_server

ローカルで動作する MCP サーバー一式です。FastAPI で提供する `manual-tools` と、クライアントアプリの `manual-tools-mcp` を 1 つのリポジトリで管理します。

## クイックスタート

```bash
git clone git@github.com:yo-mi2027/mcp_server.git
cd mcp_server
```

### manual-tools（FastAPI サーバー）

前提: Docker Desktop（もしくは互換エンジン）を起動済みで、`manuals/` と `config.yaml` が揃っていること。

#### 初回セットアップ

```bash
cd manual-tools
docker compose up --build
```

- 依存インストールとビルドで数分かかることがありますが、完了すると `http://127.0.0.1:5173` で API が立ち上がります。
- 自動リロードが有効なので `app/`・`config.yaml`・`manuals/` を編集すると数秒で反映されます。

#### 2回目以降

```bash
cd manual-tools
docker compose up
```

- `MANUAL_TOOLS_PORT=5180 docker compose up` のように環境変数でホスト側ポートを変更可能。
- バックグラウンドで動かすときは `docker compose up -d`、停止は `docker compose down`。
- 依存や `requirements.txt` を更新したときのみ `docker compose up --build` を再実行します。

### manual-tools-mcp（MCP クライアント）

前提: Node.js 18+ と npm（または互換ツール）がインストールされていること。

- ```bash
  cd manual-tools-mcp
  npm install        # 初回のみ
  npm run build      # TypeScript → build/index.js を生成
  npm start          # = node build/index.js
  ```
- Claude などの MCP クライアントからアタッチする場合は、`node /path/to/mcp_server/manual-tools-mcp/build/index.js` をコマンドとして指定してください。
- API のベース URL を切り替える場合は `MANUAL_TOOLS_BASE_URL`（推奨）または `MANUAL_TOOLS_URL` を設定してください。未設定時は `http://127.0.0.1:5173` を参照します。

## コントリビュート

1. ブランチを切る: `git checkout -b feature/...`
2. `manual-tools` / `manual-tools-mcp` それぞれの lint / test を実行
3. このリポジトリのルートでコミットして PR を作成

