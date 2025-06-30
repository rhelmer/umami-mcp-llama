# Analytics Report Generator

An automated analytics reporting tool that leverages the MCP Python SDK with Google Gemini, Ollama, or Cloudflare Workers to generate intelligent reports from Umami analytics data using the Model Control Protocol (MCP).

Blog post: https://www.rhelmer.org/blog/ai-powered-analytics-reports-using-mcp/

## Overview

This project combines several powerful tools to create automated analytics reports:

- **MCP Python SDK**: MCP client for orchestrating AI interactions
- **Google Gemini/Ollama/Cloudflare Workers**: LLM inference backends.
- **Umami MCP Server**: Connects to your Umami analytics instance to fetch website data
- **Automated Reporting**: Generates comprehensive analytics reports using AI

## Features

- 🤖 **AI-Powered Analysis**: Uses large language models to analyze website analytics data
- 📊 **Comprehensive Reports**: Generates detailed insights from your Umami analytics
- 🔄 **Flexible Backends**: Choose between Google Gemini (default), local Ollama, or Cloudflare Workers
- 💬 **Interactive Mode**: Chat interface for exploring your analytics data
- 🚀 **Easy Setup**: Simple installation and configuration process

## Prerequisites

- Python 3.8+
- Node.js and npm (for Google Gemini CLI)
- Access to an Umami analytics instance
- An AI provider:
  - A Google AI Studio API key for Gemini (recommended - generous free tier), OR
  - Ollama installed locally with a Llama model, OR
  - A Cloudflare Workers account with AI access

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Install dependencies**
   ```bash
   pip install uv
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Umami Configuration (Required)
   UMAMI_API_URL=https://your-umami-instance.com/api
   UMAMI_USERNAME=username
   UMAMI_PASSWORD=password
   UMAMI_TEAM_ID=your-team-id

   # Gemini API Configuration (Recommended - Default)
   GEMINI_API_KEY=your-gemini-api-key

   # Cloudflare AI Configuration (Alternative)
   CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
   CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
   ```

## Configuration

### Backend Setup

Clone the Umami MCP Server - Check the [Umami MCP Server documentation](https://github.com/MCP-Mirror/jakeyShakey_umami_mcp_server) for use in `--mcp-server-dir ~/src/umami_mcp_server` flag (see below).

#### Option 1: Google Gemini (Default - Recommended)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key (free tier available with generous limits)
3. Add the `GEMINI_API_KEY` to your `.env` file
4. Install the Gemini CLI:
   ```bash
   npm install -g @google/gemini-cli
   ```

#### Option 2: Ollama (Local)
```bash
# Install Ollama
## Linux
curl -fsSL https://ollama.ai/install.sh | sh
## macOS
brew install ollama

# Start Ollama service
ollama serve

# Pull Llama model
ollama pull llama3.2
```

#### Option 3: Cloudflare Workers
1. Sign up for Cloudflare Workers
2. Enable AI features in your account
3. Get your API token and account ID
4. Add credentials to `.env` file

## Usage

You can specify the AI provider using the `--ai-provider` flag. Supported providers are `gemini-cli` (default), `ollama`, and `cloudflare`.

### Interactive Chat Mode

Start an interactive session to explore your analytics data:

```bash
# Using Gemini (default - recommended)
uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server --chat

# Using Ollama
uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server --chat --ai-provider ollama

# Using Cloudflare
uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server --chat --ai-provider cloudflare
```

Example interactions:
- "Show me a summary of last month's traffic"
- "What are my top pages this week?"
- "Generate a comprehensive monthly report"
- "Compare this month's performance to last month"

### Command Line Reports

Generate specific reports directly:

```bash
# Custom date range with the default provider (Gemini)
uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server

# Specifying a different provider
uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server --ai-provider ollama
```

### Automated Scheduling

Set up automated report generation using cron:

```bash
# Add to crontab for weekly reports every Monday at 9 AM
0 9 * * 1 cd /path/to/project && uv run --with-requirements requirements.txt run.py --start-date 2025-06-01 --end-date 2025-06-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server
```

## AI Provider Comparison

| Provider             | Pros                                      | Cons                         | Best For                     |
| -------------------- | ----------------------------------------- | ---------------------------- | ---------------------------- |
| **Gemini** (Default) | Free tier, fast, high quality, easy setup | Requires internet            | Most users, production use   |
| **Ollama**           | Fully local, private, no API costs        | Requires local setup, slower | Privacy-focused, offline use |
| **Cloudflare**       | Fast, reliable, edge computing            | Usage-based pricing          | High-volume production       |

## Report Types

- **Traffic Summary**: Page views, unique visitors, sessions
- **Top Content**: Most popular pages and referrers
- **Geographic Analysis**: Visitor locations and demographics
- **Device & Browser**: Technology usage patterns
- **Performance Trends**: Growth metrics and comparisons
- **Custom Insights**: AI-generated observations and recommendations

## Troubleshooting

### Common Issues

**Gemini CLI Issues**
```bash
# Verify Gemini CLI is installed
npx @google/gemini-cli --version

# Test authentication
npx @google/gemini-cli generate -p "Hello world"
```

**Connection Errors**
```bash
# Check Umami API connectivity
curl -u user:pass https://your-umami-instance.com/api/websites
```

**Ollama Issues**
```bash
# Verify Ollama is running
ollama list
ollama ps
```

### Error Messages

- **"Gemini-CLI is not installed"**: Install with `npm install -g @google/gemini-cli`
- **"Missing GEMINI_API_KEY"**: Add your API key to the `.env` file
- **"Ollama is not installed"**: Install Ollama following the instructions above
- **"Missing CLOUDFLARE_ACCOUNT_ID"**: Add Cloudflare credentials to `.env`

## Development

### Project Structure
```
├── run.py              # Main application entry point
└── requirements.txt    # Python dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Dependencies

- `mcp`: MCP Python SDK
- `umami-mcp-server`: Umami analytics MCP server
- `python-dotenv`: Environment variable management
- `aiohttp`: Asynchronous HTTP Client/Server for asyncio and Python

## Support

For issues and questions:
- Create an issue in this repository
- Check the [Umami MCP Server documentation](https://github.com/MCP-Mirror/jakeyShakey_umami_mcp_server)
- Review [MCP Python SDK Documentation](https://pypi.org/project/mcp/)

## Acknowledgments

- [Google Gemini](https://ai.google.dev/) for the powerful and accessible AI API
- [Umami](https://umami.is/) for the analytics platform
- [Umami MCP Server](https://github.com/MCP-Mirror/jakeyShakey_umami_mcp_server) for the Umami MCP server
- [Ollama](https://ollama.ai/) for local LLM inference
- [Cloudflare](https://workers.cloudflare.com/) for cloud AI services