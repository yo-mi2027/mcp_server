# mcp_server

ローカルで動作する MCP サーバー一式です。FastAPI で提供する `manual-tools` と、クライアントアプリの `manual-tools-mcp` を 1 つのリポジトリで管理します。

## クイックスタート

```bash
git clone git@github.com:yo-mi2027/mcp_server.git
cd mcp_server
```

### 初回セットアップ（manual-tools & manual-tools-mcp）

1. **manual-tools（FastAPI サーバー）**  
   前提: Docker Desktop（もしくは互換エンジン）を起動済みで、`manuals/` と `config.yaml` が揃っていること。  
   `manuals/` はユーザー自身が使いたいファイルを入れるローカル専用ディレクトリで、Git には含めません。

   ```bash
   cd manual-tools
   docker compose up --build
   ```

   - 依存インストールとビルドで数分かかることがありますが、完了すると `http://127.0.0.1:5173` で API が立ち上がります。
   - 自動リロードが有効なので `app/`・`config.yaml`・`manuals/` を編集すると数秒で反映されます。

2. **manual-tools-mcp（MCP クライアント）**  
   前提: Node.js 18+ と npm（または互換ツール）がインストールされていること。

   ```bash
   cd manual-tools-mcp
   npm install        # 依存インストール（初回のみ）
   npm run build      # TypeScript → build/index.js を生成
   ```

### 2回目以降の起動

- **manual-tools**

  ```bash
  cd manual-tools
  docker compose up
  ```

  - `MANUAL_TOOLS_PORT=5180 docker compose up` のように環境変数でホスト側ポートを変更可能。
  - バックグラウンドで動かすときは `docker compose up -d`、停止は `docker compose down`。
  - 依存や `requirements.txt` を更新したときのみ `docker compose up --build` を再実行します。

- **manual-tools-mcp**

  ```bash
  cd manual-tools-mcp
  npm start          # = node build/index.js
  ```

  - Claude Desktop から MCP attach する場合は、`node /path/to/mcp_server/manual-tools-mcp/build/index.js` をコマンドとして指定してください（config 例: `args: [".../build/index.js"]`）。
  - API のベース URL を切り替える場合は `MANUAL_TOOLS_BASE_URL`（推奨）または `MANUAL_TOOLS_URL` を設定してください。未設定時は `http://127.0.0.1:5173` を参照します。
  - MCP ツールは `list_manuals` / `get_toc` / `list_sections` / `get_section` / `search_text` / `find_exceptions` を提供します。
    - `/resolve_reference` と `/get_outline` は FastAPI 側の HTTP では利用可能ですが、MCP では未公開です。

### プロンプト & ワークフローの管理

- 共通ハンドシェイクは `manual="運用仕様編"` の Location / Full Answer 仕様（section_id="01","02"）に集約しています。  
- 案件固有のプロンプトは基本的に Claude 側で直接記述・改善し、必要に応じて `manuals/雑務用/` に草案を残してください。  
- 再利用したいワークフローだけを別途マニュアル化したい場合は、任意の場所に `.txt` を追加し `get_section` で読ませる運用にしてください（必須ではありません）。

## コントリビュート

1. ブランチを切る: `git checkout -b feature/...`
2. `manual-tools` / `manual-tools-mcp` それぞれの lint / test を実行
3. このリポジトリのルートでコミットして PR を作成
