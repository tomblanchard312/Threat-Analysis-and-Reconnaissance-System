#!/usr/bin/env node
/**
 * Ollama Claude MCP Server
 *
 * A self-hosted Claude-like MCP server that uses Ollama's local models
 * to provide AI assistant capabilities including code generation,
 * security analysis, and shell command execution.
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const http = require('http');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || 'htb-pentest';
const MAX_TOKENS = parseInt(process.env.MAX_TOKENS) || 4096;

// System prompts for different modes
const SYSTEM_PROMPTS = {
  general: `You are Claude, an AI assistant created by Anthropic running locally via Ollama.
You are helpful, harmless, and honest. Provide clear, accurate, and helpful responses.`,

  code: `You are Claude Code, an expert programming assistant.
Generate clean, well-documented code. Explain your approach briefly.
When editing code, show only the relevant changes with context.`,

  security: `You are a security analysis assistant specialized in penetration testing.
Analyze security issues, explain vulnerabilities, and suggest remediation.
Always emphasize authorized testing only.`,

  shell: `You are a shell command assistant. Generate safe, effective shell commands.
Explain what each command does. Warn about destructive operations.
Never generate commands that could cause data loss without explicit confirmation.`
};

/**
 * Make a request to Ollama API
 */
async function ollamaRequest(endpoint, data) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint, OLLAMA_HOST);
    const postData = JSON.stringify(data);

    const options = {
      hostname: url.hostname,
      port: url.port || 11434,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          // Handle streaming response (last line is the final response)
          const lines = body.trim().split('\n');
          let fullResponse = '';
          for (const line of lines) {
            try {
              const parsed = JSON.parse(line);
              if (parsed.response) fullResponse += parsed.response;
              if (parsed.message?.content) fullResponse += parsed.message.content;
              if (parsed.done && parsed.total_duration) {
                resolve({ content: fullResponse, stats: parsed });
                return;
              }
            } catch (e) {
              // Skip non-JSON lines
            }
          }
          resolve({ content: fullResponse });
        } catch (e) {
          reject(new Error(`Failed to parse Ollama response: ${e.message}`));
        }
      });
    });

    req.on('error', (e) => reject(new Error(`Ollama request failed: ${e.message}`)));
    req.setTimeout(120000, () => {
      req.destroy();
      reject(new Error('Ollama request timed out'));
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Chat with Ollama model
 */
async function chat(prompt, systemPrompt = SYSTEM_PROMPTS.general, model = DEFAULT_MODEL) {
  const data = {
    model: model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt }
    ],
    stream: true,
    options: {
      num_predict: MAX_TOKENS,
      temperature: 0.7
    }
  };

  return await ollamaRequest('/api/chat', data);
}

/**
 * Execute a shell command safely
 */
async function executeCommand(command, workingDir = process.cwd()) {
  return new Promise((resolve, reject) => {
    // Safety checks
    const dangerousPatterns = [
      /rm\s+-rf\s+[\/~]/i,
      /mkfs/i,
      /dd\s+if=/i,
      />\s*\/dev\//i,
      /format\s+[a-z]:/i,
      /del\s+\/[sfq]/i
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(command)) {
        resolve({
          success: false,
          output: '',
          error: `Command blocked: potentially destructive operation detected. Pattern: ${pattern}`
        });
        return;
      }
    }

    exec(command, {
      cwd: workingDir,
      timeout: 60000,
      maxBuffer: 10 * 1024 * 1024 // 10MB
    }, (error, stdout, stderr) => {
      resolve({
        success: !error,
        output: stdout,
        error: error ? `${error.message}\n${stderr}` : stderr
      });
    });
  });
}

/**
 * Read a file
 */
async function readFile(filePath) {
  try {
    const absolutePath = path.resolve(filePath);
    const content = await fs.readFile(absolutePath, 'utf-8');
    const stats = await fs.stat(absolutePath);
    return {
      success: true,
      content: content,
      path: absolutePath,
      size: stats.size,
      modified: stats.mtime
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Write a file
 */
async function writeFile(filePath, content, createDirs = true) {
  try {
    const absolutePath = path.resolve(filePath);
    if (createDirs) {
      await fs.mkdir(path.dirname(absolutePath), { recursive: true });
    }
    await fs.writeFile(absolutePath, content, 'utf-8');
    return {
      success: true,
      path: absolutePath,
      size: Buffer.byteLength(content)
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * List directory contents
 */
async function listDirectory(dirPath) {
  try {
    const absolutePath = path.resolve(dirPath);
    const entries = await fs.readdir(absolutePath, { withFileTypes: true });
    const items = entries.map(entry => ({
      name: entry.name,
      type: entry.isDirectory() ? 'directory' : 'file',
      path: path.join(absolutePath, entry.name)
    }));
    return {
      success: true,
      path: absolutePath,
      items: items
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Create MCP server
const server = new Server(
  {
    name: 'ollama-claude-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
const TOOLS = [
  {
    name: 'chat',
    description: 'Chat with the local AI model for general questions and assistance',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: {
          type: 'string',
          description: 'The question or prompt to send to the AI'
        },
        mode: {
          type: 'string',
          enum: ['general', 'code', 'security', 'shell'],
          description: 'The mode/persona to use (default: general)'
        },
        model: {
          type: 'string',
          description: 'Override the default model (e.g., htb-pentest, mistral:7b)'
        }
      },
      required: ['prompt']
    }
  },
  {
    name: 'generate_code',
    description: 'Generate or modify code based on a description',
    inputSchema: {
      type: 'object',
      properties: {
        description: {
          type: 'string',
          description: 'Description of the code to generate'
        },
        language: {
          type: 'string',
          description: 'Programming language (python, javascript, bash, etc.)'
        },
        context: {
          type: 'string',
          description: 'Optional existing code or context'
        }
      },
      required: ['description']
    }
  },
  {
    name: 'analyze_security',
    description: 'Analyze code, configurations, or scan results for security issues',
    inputSchema: {
      type: 'object',
      properties: {
        content: {
          type: 'string',
          description: 'The content to analyze (code, config, scan output)'
        },
        type: {
          type: 'string',
          enum: ['code', 'config', 'scan_results', 'logs'],
          description: 'Type of content being analyzed'
        }
      },
      required: ['content']
    }
  },
  {
    name: 'shell_command',
    description: 'Execute a shell command and return the output',
    inputSchema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The shell command to execute'
        },
        workingDir: {
          type: 'string',
          description: 'Working directory for the command'
        }
      },
      required: ['command']
    }
  },
  {
    name: 'suggest_command',
    description: 'Get AI suggestions for shell commands to accomplish a task',
    inputSchema: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description: 'Description of what you want to accomplish'
        },
        platform: {
          type: 'string',
          enum: ['linux', 'windows', 'macos'],
          description: 'Target platform (default: auto-detect)'
        }
      },
      required: ['task']
    }
  },
  {
    name: 'read_file',
    description: 'Read the contents of a file',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path to the file to read'
        }
      },
      required: ['path']
    }
  },
  {
    name: 'write_file',
    description: 'Write content to a file',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path to the file to write'
        },
        content: {
          type: 'string',
          description: 'Content to write to the file'
        }
      },
      required: ['path', 'content']
    }
  },
  {
    name: 'list_directory',
    description: 'List contents of a directory',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path to the directory to list'
        }
      },
      required: ['path']
    }
  },
  {
    name: 'explain_code',
    description: 'Get an explanation of what code does',
    inputSchema: {
      type: 'object',
      properties: {
        code: {
          type: 'string',
          description: 'The code to explain'
        },
        language: {
          type: 'string',
          description: 'Programming language of the code'
        }
      },
      required: ['code']
    }
  }
];

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'chat': {
        const mode = args.mode || 'general';
        const systemPrompt = SYSTEM_PROMPTS[mode] || SYSTEM_PROMPTS.general;
        const result = await chat(args.prompt, systemPrompt, args.model);
        return {
          content: [{ type: 'text', text: result.content }]
        };
      }

      case 'generate_code': {
        const prompt = `Generate ${args.language || ''} code for the following:

${args.description}

${args.context ? `Context/existing code:\n\`\`\`\n${args.context}\n\`\`\`` : ''}

Provide clean, well-commented code. Include brief usage examples if appropriate.`;

        const result = await chat(prompt, SYSTEM_PROMPTS.code);
        return {
          content: [{ type: 'text', text: result.content }]
        };
      }

      case 'analyze_security': {
        const prompt = `Analyze the following ${args.type || 'content'} for security issues:

\`\`\`
${args.content}
\`\`\`

Identify:
1. Security vulnerabilities or misconfigurations
2. Severity level (Critical, High, Medium, Low, Info)
3. Potential attack vectors
4. Recommended fixes or mitigations

Be specific and actionable in your analysis.`;

        const result = await chat(prompt, SYSTEM_PROMPTS.security);
        return {
          content: [{ type: 'text', text: result.content }]
        };
      }

      case 'shell_command': {
        const result = await executeCommand(args.command, args.workingDir);
        const output = result.success
          ? `Command executed successfully:\n\n${result.output || '(no output)'}`
          : `Command failed:\n\n${result.error}`;
        return {
          content: [{ type: 'text', text: output }]
        };
      }

      case 'suggest_command': {
        const platform = args.platform || (process.platform === 'win32' ? 'windows' : 'linux');
        const prompt = `Suggest shell commands to accomplish this task on ${platform}:

Task: ${args.task}

Provide:
1. The exact command(s) to run
2. Brief explanation of what each command does
3. Any warnings or prerequisites
4. Alternative approaches if applicable`;

        const result = await chat(prompt, SYSTEM_PROMPTS.shell);
        return {
          content: [{ type: 'text', text: result.content }]
        };
      }

      case 'read_file': {
        const result = await readFile(args.path);
        if (result.success) {
          return {
            content: [{
              type: 'text',
              text: `File: ${result.path}\nSize: ${result.size} bytes\nModified: ${result.modified}\n\n${result.content}`
            }]
          };
        } else {
          return {
            content: [{ type: 'text', text: `Error reading file: ${result.error}` }],
            isError: true
          };
        }
      }

      case 'write_file': {
        const result = await writeFile(args.path, args.content);
        if (result.success) {
          return {
            content: [{
              type: 'text',
              text: `File written successfully: ${result.path} (${result.size} bytes)`
            }]
          };
        } else {
          return {
            content: [{ type: 'text', text: `Error writing file: ${result.error}` }],
            isError: true
          };
        }
      }

      case 'list_directory': {
        const result = await listDirectory(args.path);
        if (result.success) {
          const listing = result.items.map(item =>
            `${item.type === 'directory' ? '[DIR]' : '[FILE]'} ${item.name}`
          ).join('\n');
          return {
            content: [{
              type: 'text',
              text: `Directory: ${result.path}\n\n${listing || '(empty)'}`
            }]
          };
        } else {
          return {
            content: [{ type: 'text', text: `Error listing directory: ${result.error}` }],
            isError: true
          };
        }
      }

      case 'explain_code': {
        const prompt = `Explain the following ${args.language || ''} code:

\`\`\`${args.language || ''}
${args.code}
\`\`\`

Provide:
1. High-level overview of what the code does
2. Step-by-step explanation of key parts
3. Any notable patterns or techniques used
4. Potential issues or improvements`;

        const result = await chat(prompt, SYSTEM_PROMPTS.code);
        return {
          content: [{ type: 'text', text: result.content }]
        };
      }

      default:
        return {
          content: [{ type: 'text', text: `Unknown tool: ${name}` }],
          isError: true
        };
    }
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Ollama Claude MCP server started');
  console.error(`Using Ollama at: ${OLLAMA_HOST}`);
  console.error(`Default model: ${DEFAULT_MODEL}`);
}

main().catch(console.error);
