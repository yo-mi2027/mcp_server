"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
// src/index.ts
var mcp_js_1 = require("@modelcontextprotocol/sdk/server/mcp.js");
var stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
var zod_1 = require("zod");
// Python FastAPI サーバーのベースURL
// 何も指定しない場合は http://127.0.0.1:5173 を使う
var BASE_URL = (_a = process.env.MANUAL_TOOLS_BASE_URL) !== null && _a !== void 0 ? _a : "http://127.0.0.1:5173";
// 共通の HTTP ヘルパー
function getJson(path) {
    return __awaiter(this, void 0, void 0, function () {
        var url, res;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    url = "".concat(BASE_URL).concat(path);
                    return [4 /*yield*/, fetch(url)];
                case 1:
                    res = _a.sent();
                    if (!res.ok) {
                        throw new Error("HTTP ".concat(res.status, " when calling ").concat(url));
                    }
                    return [4 /*yield*/, res.json()];
                case 2: return [2 /*return*/, (_a.sent())];
            }
        });
    });
}
// MCP サーバ本体
var server = new mcp_js_1.McpServer({
    name: "manual-tools", // MCP サーバ名（Claude 側に表示される）
    version: "0.1.0",
});
// ---- Tool: list_manuals -------------------------------------------------
// FastAPI の GET /list_manuals をそのまま叩くラッパー
server.registerTool("list_manuals", {
    title: "List manuals",
    description: "ローカル FastAPI manual-tools サーバから、利用可能なマニュアル名一覧を取得します。",
    // 引数は無し
    inputSchema: {},
    // 返り値の構造（任意だが、書いておくとクライアント側が理解しやすい）
    outputSchema: {
        manuals: zod_1.z.array(zod_1.z.string()),
    },
}, function () { return __awaiter(void 0, void 0, void 0, function () {
    var manuals, output;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, getJson("/list_manuals")];
            case 1:
                manuals = _a.sent();
                output = { manuals: manuals };
                // content は LLM に見せるテキスト
                // structuredContent は「構造化された結果」で、対応クライアントがあればそのまま扱える
                return [2 /*return*/, {
                        content: [
                            {
                                type: "text",
                                text: manuals.join(", "),
                            },
                        ],
                        structuredContent: output,
                    }];
        }
    });
}); });
// ---- メイン処理（stdio トランスポートで起動） ------------------------
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var transport;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    transport = new stdio_js_1.StdioServerTransport();
                    return [4 /*yield*/, server.connect(transport)];
                case 1:
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    });
}
main().catch(function (err) {
    console.error("Fatal error in manual-tools MCP server:", err);
    process.exit(1);
});
