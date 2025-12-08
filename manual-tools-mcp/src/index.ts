import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Base URL of the local Python FastAPI backend server.
const BASE_URL =
  process.env.MANUAL_TOOLS_BASE_URL ??
  process.env.MANUAL_TOOLS_URL ??
  "http://127.0.0.1:5173";

// ---------------------------------------------------------------------
// Shared HTTP helpers
// ---------------------------------------------------------------------

// Shared HTTP helper (GET → JSON)
async function getJson<T>(
  path: string,
  query?: Record<string, string>
): Promise<T> {
  const url = new URL(path, BASE_URL);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url);
  const txt = await res.text();

  if (!res.ok) {
    // Include some of the response body to make errors easier to debug on the client side.
    throw new Error(
      `HTTP ${res.status} when calling ${url.toString()}: ${txt.slice(
        0,
        200
      )}`
    );
  }

  return JSON.parse(txt) as T;
}

// Shared HTTP helper (POST → JSON)
async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = new URL(path, BASE_URL);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const txt = await res.text();

  if (!res.ok) {
    throw new Error(
      `HTTP ${res.status} when calling ${url.toString()}: ${txt.slice(
        0,
        200
      )}`
    );
  }

  return JSON.parse(txt) as T;
}

// ---------------------------------------------------------------------
// FastAPI response types (approximate shapes, kept in sync with backend)
// ---------------------------------------------------------------------

type TocItem = {
  id: string;
  title: string;
  file: string;
  children?: unknown[] | null;
};

type GetTocResponse = {
  manual: string;
  toc: TocItem[];
};

type ListSectionsResponse = {
  manual: string;
  sections: string[];
};

type GetSectionResponse = {
  manual: string;
  section_id: string;
  title: string;
  text: string;
  file?: string;
  encoding?: string;
  id?: string;
};

type SearchTextResult = {
  section_id: string;
  snippet: string;
};

type SearchTextResponse = {
  results: SearchTextResult[];
};

type FindExceptionsResult = {
  section_id: string;
  text: string;
};

type FindExceptionsResponse = {
  results: FindExceptionsResult[];
};

// ---------------------------------------------------------------------
// MCP server
// ---------------------------------------------------------------------

const server = new McpServer({
  name: "manual-tools",
  version: "0.1.0",
  description: [
    "Tools for querying structured local manuals via a Python FastAPI backend.",
    "These tools are designed to support a hierarchical reasoning RAG workflow with two modes:",
    "Location Mode (find all relevant sections) and Full Answer Mode (read those sections in detail and enumerate all relevant elements).",
    "When the user asks a question about a manual (for example the manual '給付金編'),",
    "you SHOULD first consult the operation-spec manual '運用仕様編' if it exists,",
    "by reading the following sections via get_section:",
    " - Location Mode specification:   manual_name='運用仕様編', section_id='01'",
    " - Full Answer Mode specification: manual_name='運用仕様編', section_id='02'",
    "After that, apply any task-specific prompts provided by the user (for example ad-hoc instructions pasted in the chat or stored in雑務用), then follow the specifications:",
    " - In Location Mode, use get_toc, search_text, find_exceptions, and (light) get_section calls",
    "   to build S0 (initial candidates) and S1 (final relevant section list) using the exploration and screening phases.",
    " - In Full Answer Mode, treat S1 as input, call get_section to read each section in full,",
    "   conceptually chunk the text, extract conditions/definitions/exceptions,",
    "   and build a chapter-wise structured list of elements as the main answer.",
  ].join(" "),
});

// =====================================================================
// list_manuals
// =====================================================================

server.registerTool(
  "list_manuals",
  {
    title: "List manuals",
    description:
      "Return the list of available manual names. Use this first to discover manuals such as '給付金編' or the operation-spec manual '運用仕様編'.",
    // No arguments
    inputSchema: {},
    outputSchema: {
      manuals: z
        .array(z.string())
        .describe("Array of manual names available on the backend."),
    },
  },
  async () => {
    const manuals = await getJson<string[]>("/list_manuals");
    const structuredContent = { manuals };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// get_toc
// =====================================================================

server.registerTool(
  "get_toc",
  {
    title: "Get table of contents",
    description: [
      "Get the table of contents (TOC) for a given manual.",
      "Each TOC item includes the section ID, title, and underlying text file name, plus optional children.",
      "In the hierarchical RAG flow, call this early to understand the structure of the manual",
      "before selecting sections and calling get_section.",
    ].join(" "),
    inputSchema: {
      manual_name: z
        .string()
        .describe(
          "Name of the manual to query (for example '給付金編' or '運用仕様編')."
        ),
    },
    outputSchema: {
      manual: z.string().describe("Name of the manual."),
      toc: z
        .array(
          z.object({
            id: z.string().describe("Section ID (section_id)."),
            title: z.string().describe("Section title."),
            file: z
              .string()
              .describe(
                "Text file name for this section (relative to the manual directory)."
              ),
            children: z
              .array(z.any())
              .nullable()
              .optional()
              .describe(
                "Optional children for hierarchical TOC (usually null or empty for now)."
              ),
          })
        )
        .describe("Array of TOC items for the manual."),
    },
  },
  async ({ manual_name }) => {
    const resp = await getJson<GetTocResponse>("/get_toc", { manual_name });
    const structuredContent = resp;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// list_sections
// =====================================================================

server.registerTool(
  "list_sections",
  {
    title: "List section IDs",
    description: [
      "Return the list of section IDs (section_id) for the specified manual.",
      "This is essentially a flattened view of the TOC IDs.",
    ].join(" "),
    inputSchema: {
      manual_name: z
        .string()
        .describe("Name of the manual whose section IDs you want to list."),
    },
    outputSchema: {
      manual: z.string().describe("Name of the manual."),
      sections: z
        .array(z.string())
        .describe("Array of section IDs (section_id strings)."),
    },
  },
  async ({ manual_name }) => {
    const resp = await getJson<ListSectionsResponse>("/list_sections", {
      manual_name,
    });
    const structuredContent = resp;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// get_section
// =====================================================================

server.registerTool(
  "get_section",
  {
    title: "Get section text",
    description: [
      "Retrieve the full text of a specific section (chapter) from the specified manual.",
      "In Location Mode, use this lightly for screening: confirm whether a candidate section actually discusses the question’s theme.",
      "In Full Answer Mode, call this for every section in S1, treat the returned text as the full body of the section,",
      "and conceptually chunk it to extract conditions, definitions, exceptions, and other elements.",
    ].join(" "),
    inputSchema: {
      manual_name: z
        .string()
        .describe("Name of the manual containing the target section."),
      section_id: z
        .string()
        .describe("Section ID (for example '03-1')."),
    },
    outputSchema: {
      manual: z.string().describe("Name of the manual."),
      section_id: z
        .string()
        .describe("Section ID of the returned section."),
      title: z.string().describe("Title of the section."),
      text: z
        .string()
        .describe(
          "Full text of the section, with normalized newlines. This is the primary source for reading rules."
        ),
      file: z
        .string()
        .optional()
        .describe(
          "Underlying text file name for the section, if provided by the backend."
        ),
      encoding: z
        .string()
        .optional()
        .describe("Encoding used for the source text (e.g. 'utf-8')."),
      id: z
        .string()
        .optional()
        .describe(
          "Optional backend identifier for the section (defaults to section_id)."
        ),
    },
  },
  async ({ manual_name, section_id }) => {
    const resp = await getJson<GetSectionResponse>("/get_section", {
      manual_name,
      section_id,
    });
    const structuredContent = resp;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// search_text
// =====================================================================

server.registerTool(
  "search_text",
  {
    title: "Search text in manual",
    description: [
      "Full-text search within the specified manual.",
      "Use this to locate candidate sections and snippets related to the user’s question.",
      "Supports three modes:",
      " - 'plain': simple substring search.",
      " - 'regex': regular expression search (invalid patterns fall back to plain search on the backend).",
      " - 'loose': tolerant matching that ignores spaces and some punctuation (useful for noisy OCR text).",
      "In the hierarchical RAG flow, this tool is mainly used in Location Mode during the exploration phase",
      "to build the initial candidate set S0 of section_ids based on the question.",
    ].join(" "),
    inputSchema: {
      manual_name: z
        .string()
        .describe("Name of the manual to search within."),
      query: z
        .string()
        .describe(
          "Search query string (plain text or regex pattern depending on 'mode')."
        ),
      section_id: z
        .string()
        .optional()
        .describe(
          "Optional section ID. If provided, restrict the search to this single section."
        ),
      case_sensitive: z
        .boolean()
        .optional()
        .describe(
          "When true, perform a case-sensitive search (backend default is false)."
        ),
      mode: z
        .enum(["plain", "regex", "loose"])
        .optional()
        .describe(
          "Search mode. If omitted, the backend default (typically 'regex') will be used."
        ),
      limit: z
        .number()
        .int()
        .positive()
        .optional()
        .describe(
          "Maximum number of results to return. If omitted, the backend default is used."
        ),
    },
    outputSchema: {
      results: z
        .array(
          z.object({
            section_id: z
              .string()
              .describe("Section ID where the hit occurred."),
            snippet: z
              .string()
              .describe(
                "Excerpt of text around the first match in that section, used for context and screening."
              ),
          })
        )
        .describe(
          "Array of search hits, each containing a section_id and a snippet around the match."
        ),
    },
  },
  async ({ manual_name, query, section_id, case_sensitive, mode, limit }) => {
    const body: Record<string, unknown> = {
      manual_name,
      query,
    };

    if (section_id) body.section_id = section_id;
    if (typeof case_sensitive === "boolean")
      body.case_sensitive = case_sensitive;
    if (mode) body.mode = mode;
    if (typeof limit === "number") body.limit = limit;

    const resp = await postJson<SearchTextResponse>("/search_text", body);
    const structuredContent = resp;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// find_exceptions
// =====================================================================

server.registerTool(
  "find_exceptions",
  {
    title: "Find exceptions / exclusions",
    description: [
      "Extract passages related to exceptions, exclusions, non-covered cases, or caution notes from the specified manual.",
      "The backend scans for predefined exception-related vocabulary (e.g., '注意', '留意', '支払われない', '対象外', '不適用', '除外').",
      "In Location Mode, use this alongside search_text to ensure that exception-related sections are not missed.",
      "In Full Answer Mode, use this to identify candidate chunks describing exceptions or non-coverage,",
      "and then read them carefully via get_section to integrate them into the final structured list of elements.",
    ].join(" "),
    inputSchema: {
      manual_name: z
        .string()
        .describe("Name of the manual to scan for exception-related passages."),
      section_id: z
        .string()
        .optional()
        .describe(
          "Optional section ID. If provided, restrict extraction to this single section."
        ),
      limit: z
        .number()
        .int()
        .positive()
        .optional()
        .describe(
          "Maximum number of results to return. If omitted, the backend default is used."
        ),
    },
    outputSchema: {
      results: z
        .array(
          z.object({
            section_id: z
              .string()
              .describe("Section ID where the exception-related text was found."),
            text: z
              .string()
              .describe(
                "Text block containing the exception-related description and its surrounding context."
              ),
          })
        )
        .describe(
          "Array of exception-related candidates, each tied to a section_id and a context text block."
        ),
    },
  },
  async ({ manual_name, section_id, limit }) => {
    const body: Record<string, unknown> = {
      manual_name,
    };

    if (section_id) body.section_id = section_id;
    if (typeof limit === "number") body.limit = limit;

    const resp = await postJson<FindExceptionsResponse>(
      "/find_exceptions",
      body
    );
    const structuredContent = resp;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  }
);

// =====================================================================
// Main: connect to the client over stdio
// =====================================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal error in manual-tools MCP server:", err);
  process.exit(1);
});