import asyncio
import os
import json
import aiohttp
import warnings
import argparse
from pathlib import Path
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

# Suppress specific warnings
warnings.filterwarnings(
    "ignore", category=UserWarning, module="multiprocessing.resource_tracker"
)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class AnalyticsDashboard:
    def __init__(self, mcp_server_dir: str):
        self.mcp_server_dir = mcp_server_dir
        self.setup_mcp_server()
        self.setup_ai_clients()
        self.session_data = {}  # Store data for chat mode

    def setup_mcp_server(self):
        """Setup MCP server parameters"""
        keys = [
            "TOKENIZERS_PARALLELISM",
            "UMAMI_API_URL",
            "UMAMI_USERNAME",
            "UMAMI_PASSWORD",
            "UMAMI_TEAM_ID",
        ]
        env_vars = {k: os.environ[k] for k in keys if k in os.environ}

        self.server_params = StdioServerParameters(
            command="uv",
            args=[
                "--directory",
                self.mcp_server_dir,
                "run",
                "analytics-service",
            ],
            env=env_vars,
        )

    def setup_ai_clients(self):
        """Setup AI client configurations"""
        self.CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

    async def call_cloudflare_ai(
        self, prompt: str, model: str = "@cf/meta/llama-3.1-8b-instruct"
    ) -> str:
        """Call Cloudflare Workers AI"""
        if not self.CLOUDFLARE_ACCOUNT_ID or not self.CLOUDFLARE_API_TOKEN:
            raise ValueError(
                "Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN environment variables"
            )

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"

        headers = {
            "Authorization": f"Bearer {self.CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "temperature": 0.1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Cloudflare AI error ({response.status}): {error_text}"
                    )

                result = await response.json()
                if not result.get("success"):
                    raise RuntimeError(f"Cloudflare AI API error: {result}")

                return result["result"]["response"].strip()

    async def call_ollama_fallback(self, prompt: str, model: str = "llama3.2") -> str:
        """Fallback to Ollama if Cloudflare AI fails"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "run",
                model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate(input=prompt.encode())

            if proc.returncode != 0:
                raise RuntimeError(f"Ollama error: {stderr.decode()}")

            return stdout.decode().strip()
        except FileNotFoundError:
            raise RuntimeError("Ollama is not installed or not in PATH")

    async def call_ai_with_fallback(self, prompt: str) -> Tuple[str, str]:
        """Try Cloudflare AI first, fallback to Ollama"""
        try:
            response = await self.call_cloudflare_ai(prompt)
            return response, "cloudflare"
        except Exception as cf_error:
            print(f"Cloudflare AI failed: {cf_error}")
            print("Falling back to Ollama...")
            try:
                response = await self.call_ollama_fallback(prompt)
                return response, "ollama"
            except Exception as ollama_error:
                raise RuntimeError(
                    f"Both AI services failed. Cloudflare: {cf_error}, Ollama: {ollama_error}"
                )

    def get_website_id_from_domain(
        self, websites_data: list, domain: str
    ) -> Optional[str]:
        """Extract website ID from the websites list based on domain"""
        try:
            if isinstance(websites_data, list) and len(websites_data) > 0:
                # Handle the case where websites_data is wrapped in TextContent
                websites_content = websites_data[0]
                if hasattr(websites_content, "text"):
                    websites_json = json.loads(websites_content.text)
                    for website in websites_json.get("data", []):
                        if website.get("domain") == domain:
                            return website.get("id")
            return None
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            print(f"Error parsing websites data: {e}")
            return None

    async def get_real_data_from_mcp(
        self,
        session: ClientSession,
        website_domain: str,
        start_date: str,
        end_date: str,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """Get real data from MCP server with proper error handling"""
        real_data = {
            "website_domain": website_domain,
            "date_range": f"{start_date} to {end_date}",
            "timezone": timezone,
        }

        try:
            # List available tools
            tools_response = await session.list_tools()
            available_tools = [tool.name for tool in tools_response.tools]
            print(f"Available MCP tools: {available_tools}")
            real_data["available_tools"] = available_tools

            # Get website HTML contents
            if "get_html" in available_tools:
                try:
                    html_result = await session.call_tool("get_html", {})
                    real_data["html"] = html_result.content
                except Exception as e:
                    print(f"Error getting html: {e}")
                    real_data["html_error"] = str(e)
                    return real_data

            # Get website list to find the correct website ID
            if "get_websites" in available_tools:
                try:
                    websites_result = await session.call_tool("get_websites", {})
                    real_data["websites"] = websites_result.content
                    print(f"Available websites: {len(websites_result.content)} found")

                    # Extract website ID for the domain
                    website_id = self.get_website_id_from_domain(
                        websites_result.content, website_domain
                    )
                    if website_id:
                        real_data["website_id"] = website_id
                        print(f"Found website ID for {website_domain}: {website_id}")
                    else:
                        print(f"Could not find website ID for domain: {website_domain}")
                        return real_data

                except Exception as e:
                    print(f"Error getting websites: {e}")
                    real_data["websites_error"] = str(e)
                    return real_data

            # Now try other endpoints with the correct website_id and parameters
            website_id = real_data.get("website_id")
            if not website_id:
                print("No website ID available, skipping other API calls")
                return real_data

            # Get website stats with proper parameters
            if "get_website_stats" in available_tools:
                try:
                    stats_result = await session.call_tool(
                        "get_website_stats",
                        {
                            "website_id": website_id,
                            "start_at": start_date,
                            "end_at": end_date,
                        },
                    )
                    real_data["website_stats"] = stats_result.content
                    print(f"Successfully retrieved website stats")
                except Exception as e:
                    print(f"Error getting website stats: {e}")
                    real_data["stats_error"] = str(e)

            # Get pageview series with proper parameters
            if "get_pageview_series" in available_tools:
                try:
                    pageview_result = await session.call_tool(
                        "get_pageview_series",
                        {
                            "website_id": website_id,
                            "start_at": start_date,
                            "end_at": end_date,
                            "unit": "day",  # or "hour", "month"
                            "timezone": timezone,
                        },
                    )
                    real_data["pageview_series"] = pageview_result.content
                    print(f"Successfully retrieved pageview series")
                except Exception as e:
                    print(f"Error getting pageview series: {e}")
                    real_data["pageview_error"] = str(e)

            # Get website metrics with proper parameters
            if "get_website_metrics" in available_tools:
                try:
                    # Try different metric types
                    for metric_type in [
                        "url",
                        "referrer",
                        "browser",
                        "os",
                        "device",
                        "country",
                    ]:
                        try:
                            metrics_result = await session.call_tool(
                                "get_website_metrics",
                                {
                                    "website_id": website_id,
                                    "start_at": start_date,
                                    "end_at": end_date,
                                    "type": metric_type,
                                },
                            )
                            real_data[f"metrics_{metric_type}"] = metrics_result.content
                            print(f"Successfully retrieved {metric_type} metrics")
                            break  # Get at least one metric type
                        except Exception as e:
                            continue
                except Exception as e:
                    print(f"Error getting website metrics: {e}")
                    real_data["metrics_error"] = str(e)

            # Get active visitors (this might still fail based on your output)
            if "get_active_visitors" in available_tools:
                try:
                    active_result = await session.call_tool(
                        "get_active_visitors", {"website_id": website_id}
                    )
                    real_data["active_visitors"] = active_result.content
                    print(f"Successfully retrieved active visitors")
                except Exception as e:
                    print(f"Error getting active visitors (expected): {e}")
                    real_data["active_visitors_error"] = str(e)

        except Exception as e:
            print(f"Error getting real data: {e}")
            real_data["general_error"] = str(e)

        return real_data

    async def create_validation_prompt(
        self, mcp_prompt: str, real_data: Dict[str, Any]
    ) -> str:
        """Create a comprehensive validation prompt"""
        real_data_str = json.dumps(real_data, indent=2, default=str)

        prompt = f"""You are an expert analytics consultant creating a dashboard based on REAL data from an analytics system.

DASHBOARD CREATION GUIDE:
{mcp_prompt}

ACTUAL DATA FROM ANALYTICS SYSTEM:
{real_data_str}

CRITICAL REQUIREMENTS:
1. ONLY use the real data provided above - NEVER fabricate numbers
2. If data is missing/unavailable, clearly state this and explain why
3. Provide actionable insights based on available data
4. Suggest specific next steps for missing data
5. Create visualizations only for data that actually exists
6. Be transparent about data limitations

ANALYSIS TARGET:
- Website: {real_data.get('website_domain', 'Unknown')}
- Period: {real_data.get('date_range', 'Unknown')}
- Timezone: {real_data.get('timezone', 'Unknown')}

Create a comprehensive dashboard analysis using ONLY the real data provided."""
        print("debug prompt:", prompt)
        return prompt

    async def create_chat_prompt(self, user_question: str) -> str:
        """Create a chat prompt with context from the session data"""
        real_data_str = json.dumps(self.session_data, indent=2, default=str)

        return f"""You are an expert analytics consultant answering questions about website analytics data.

CONTEXT - AVAILABLE DATA:
{real_data_str}

USER QUESTION: {user_question}

GUIDELINES:
1. Answer based ONLY on the real data provided above
2. If the data doesn't contain information to answer the question, say so clearly
3. Provide specific insights and recommendations when possible
4. Suggest what additional data might be needed if the question can't be fully answered
5. Be conversational but professional
6. Refer to specific metrics and time periods from the data when relevant

Answer the user's question about the website analytics:"""

    def detect_hallucinations(self, ai_response: str) -> list:
        """Enhanced hallucination detection"""
        hallucination_indicators = [
            # Common fake numbers
            "1,234,567",
            "45,678",
            "12,345",
            "100,000",
            "50,000",
            # Generic metrics without real data
            "Total pageviews: 1",
            "Unique visitors: 1",
            # Placeholder language
            "fictional",
            "example data",
            "placeholder",
            "sample data",
            "dummy data",
            "test data",
            "mock data",
            # Vague time references without real data
            "peak hours",
            "busy periods",
            "high traffic times",
            # Made-up percentages
            "45% increase",
            "30% bounce rate",
            "25% growth",
        ]

        found_indicators = []
        for indicator in hallucination_indicators:
            if indicator.lower() in ai_response.lower():
                found_indicators.append(indicator)

        return found_indicators

    async def chat_mode(self):
        """Interactive chat mode for asking questions about the data"""
        print("\n🤖 Entering chat mode! Ask questions about your analytics data.")
        print("Type 'quit', 'exit', or 'q' to leave chat mode.\n")

        while True:
            try:
                user_input = input("\n📊 Your question: ").strip()

                if user_input.lower() in ["quit", "exit", "q", ""]:
                    print("👋 Exiting chat mode. Goodbye!")
                    break

                # Create chat prompt with context
                chat_prompt = await self.create_chat_prompt(user_input)

                # Get AI response
                print("\n🤔 Thinking...")
                ai_response, ai_provider = await self.call_ai_with_fallback(chat_prompt)

                print(f"\n💬 {ai_provider.upper()} Response:")
                print("-" * 50)
                print(ai_response)
                print("-" * 50)

            except KeyboardInterrupt:
                print("\n\n👋 Exiting chat mode. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error in chat: {e}")
                continue

    async def create_dashboard(
        self,
        website_domain: str,
        start_date: str,
        end_date: str,
        timezone: str = "UTC",
        enable_chat: bool = False,
    ):
        """Main method to create dashboard"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    print("✅ Connected to MCP server")

                    # Initialize session
                    try:
                        await session.initialize()
                        print("✅ Session initialized")
                    except Exception as init_error:
                        print(f"❌ Initialization error: {init_error}")
                        return

                    # Get real data
                    print(f"\n📊 Getting real data for {website_domain}...")
                    real_data = await self.get_real_data_from_mcp(
                        session, website_domain, start_date, end_date, timezone
                    )

                    # Store data for chat mode
                    self.session_data = real_data

                    # Get MCP dashboard prompt
                    try:
                        prompts_response = await session.list_prompts()
                        prompts = [p.name for p in prompts_response.prompts]
                        print(f"📋 Available prompts: {prompts}")

                        if "Create Dashboard" in prompts:
                            dashboard_args = {
                                "Website Name": website_domain,
                                "Start Date (YYYY-MM-DD)": start_date,
                                "End Date (YYYY-MM-DD)": end_date,
                                "Timezone": timezone,
                            }

                            prompt_response = await session.get_prompt(
                                "Create Dashboard", dashboard_args
                            )

                            if prompt_response.messages:
                                message_content = prompt_response.messages[0].content
                                mcp_prompt = getattr(
                                    message_content, "text", str(message_content)
                                )

                                # Create validation prompt
                                validation_prompt = await self.create_validation_prompt(
                                    mcp_prompt, real_data
                                )

                                # Get AI response
                                print("\n🤖 Generating dashboard with AI...")
                                ai_response, ai_provider = (
                                    await self.call_ai_with_fallback(validation_prompt)
                                )

                                print(
                                    f"\n📈 DASHBOARD ANALYSIS ({ai_provider.upper()}):"
                                )
                                print("=" * 80)
                                print(ai_response)
                                print("=" * 80)

                                # Check for hallucinations
                                hallucination_indicators = self.detect_hallucinations(
                                    ai_response
                                )
                                if hallucination_indicators:
                                    print(
                                        f"\n⚠️  Potential data fabrication detected: {hallucination_indicators}"
                                    )
                                else:
                                    print(
                                        "\n✅ Analysis appears to be based on real data"
                                    )

                                # Enter chat mode if enabled
                                if enable_chat:
                                    await self.chat_mode()

                            else:
                                print("❌ No content in prompt result")
                        else:
                            print("❌ 'Create Dashboard' prompt not available")

                    except Exception as prompt_error:
                        print(f"❌ Error with prompts: {prompt_error}")

        except Exception as e:
            print(f"❌ Error in dashboard creation: {e}")
            import traceback

            traceback.print_exc()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Analytics Dashboard Generator")

    parser.add_argument(
        "--mcp-server-dir",
        default="/Users/example/src/jakeyShakey_umami_mcp_server/",
        help="Path to MCP server directory",
    )
    parser.add_argument(
        "--website", default="example.com", help="Website domain to analyze"
    )
    parser.add_argument(
        "--start-date", default="2025-06-01", help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", default="2025-07-01", help="End date (YYYY-MM-DD)"
    )
    parser.add_argument("--timezone", default="UTC", help="Timezone for analysis")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Enable interactive chat mode after generating report",
    )

    return parser.parse_args()


async def main():
    """Main function with command-line argument parsing"""
    args = parse_arguments()

    print(f"🚀 Starting Analytics Dashboard")
    print(f"   Website: {args.website}")
    print(f"   Date Range: {args.start_date} to {args.end_date}")
    print(f"   Timezone: {args.timezone}")
    print(f"   Chat Mode: {'Enabled' if args.chat else 'Disabled'}")
    print()

    # Create dashboard
    dashboard = AnalyticsDashboard(args.mcp_server_dir)
    await dashboard.create_dashboard(
        args.website, args.start_date, args.end_date, args.timezone, args.chat
    )


if __name__ == "__main__":
    asyncio.run(main())
