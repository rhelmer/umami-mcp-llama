# Analytics Report Generator

An automated analytics reporting tool that leverages MiraScope with Ollama or Cloudflare Workers to generate intelligent reports from Umami analytics data using the Model Control Protocol (MCP).

## Overview

This project combines several powerful tools to create automated analytics reports:

- **MiraScope**: MCP client for orchestrating AI interactions
- **Ollama/Cloudflare Workers**: LLM inference backends for running Llama models
- **Umami MCP Server**: Connects to your Umami analytics instance to fetch website data
- **Automated Reporting**: Generates comprehensive analytics reports using AI

## Features

- 🤖 **AI-Powered Analysis**: Uses Llama models to analyze website analytics data
- 📊 **Comprehensive Reports**: Generates detailed insights from your Umami analytics
- 🔄 **Flexible Backends**: Choose between local Ollama or cloud-based Cloudflare Workers
- 💬 **Interactive Mode**: Chat interface for exploring your analytics data
- 🚀 **Easy Setup**: Simple installation and configuration process

## Prerequisites

- Python 3.8+
- Access to an Umami analytics instance
- Either:
  - Ollama installed locally with Llama model, OR
  - Cloudflare Workers account with AI access

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
   # Umami Configuration
   UMAMI_API_URL=https://your-umami-instance.com/api
   UMAMI_USERNAME=username
   UMAMI_PASSWORD=password
   UMAMI_TEAM_ID=your-team-id
   ```

## Configuration

### Backend Setup

#### Option 1: Ollama (Local)
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

#### Option 2: Cloudflare Workers
1. Sign up for Cloudflare Workers
2. Enable AI features in your account
3. Get your API token and account ID
4. Add credentials to `.env` file

## Usage

### Interactive Chat Mode

Start an interactive session to explore your analytics data:

```bash
uv run --with-requirements requirements.txt run.py --start-date 2024-01-01 --end-date 2024-01-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server --chat
```

Example interactions:
- "Show me a summary of last month's traffic"
- "What are my top pages this week?"
- "Generate a comprehensive monthly report"
- "Compare this month's performance to last month"

### Command Line Reports

Generate specific reports directly:

```bash
# Custom date range
uv run --with-requirements requirements.txt run.py --start-date 2024-01-01 --end-date 2024-01-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server
```

### Automated Scheduling

Set up automated report generation using cron:

```bash
# Add to crontab for weekly reports every Monday at 9 AM
0 9 * * 1 cd /path/to/project && uv run --with-requirements requirements.txt run.py --start-date 2024-01-01 --end-date 2024-01-31 --website example.com --mcp-server-dir ~/src/umami_mcp_server

```

## Report Types

- **Traffic Summary**: Page views, unique visitors, sessions
- **Top Content**: Most popular pages and referrers
- **Geographic Analysis**: Visitor locations and demographics
- **Device & Browser**: Technology usage patterns
- **Performance Trends**: Growth metrics and comparisons
- **Custom Insights**: AI-generated observations and recommendations

## Troubleshooting

### Common Issues

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

- `miracope`: MCP client framework
- `umami-mcp-server`: Umami analytics MCP integration
- `python-dotenv`: Environment variable management

## Support

For issues and questions:
- Create an issue in this repository
- Check the [Umami MCP Server documentation](https://github.com/MCP-Mirror/jakeyShakey_umami_mcp_server)
- Review [MiraScope documentation](https://mirascope.com/docs/mirascope)

## Acknowledgments

- [Umami](https://umami.is/) for the analytics platform
- [MCP Mirror](https://github.com/MCP-Mirror) for the Umami MCP server
- [Ollama](https://ollama.ai/) for local LLM inference
- [Cloudflare](https://workers.cloudflare.com/) for cloud AI services