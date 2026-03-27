# TradingAgents — Comprehensive Project Summary

> **Version:** 0.2.2  
> **Origin:** [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) — arXiv: [2412.20138](https://arxiv.org/abs/2412.20138)  
> **License:** See `LICENSE`  
> **Python:** ≥ 3.10  
> **Generated:** 2026-03-27  

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)  
2. [Architecture at a Glance](#2-architecture-at-a-glance)  
3. [Directory Structure](#3-directory-structure)  
4. [Core Pipeline & Execution Flow](#4-core-pipeline--execution-flow)  
5. [Agent Taxonomy (All Agents)](#5-agent-taxonomy-all-agents)  
   - 5.1 [Analyst Team](#51-analyst-team)  
   - 5.2 [Researcher Team](#52-researcher-team)  
   - 5.3 [Trader Agent](#53-trader-agent)  
   - 5.4 [Risk Management Team](#54-risk-management-team)  
   - 5.5 [Portfolio Manager](#55-portfolio-manager)  
6. [State Management & Data Model](#6-state-management--data-model)  
7. [Data Layer (`dataflows/`)](#7-data-layer-dataflows)  
   - 7.1 [Vendor Abstraction & Routing](#71-vendor-abstraction--routing)  
   - 7.2 [yfinance Provider](#72-yfinance-provider)  
   - 7.3 [Alpha Vantage Provider](#73-alpha-vantage-provider)  
   - 7.4 [Technical Indicators](#74-technical-indicators)  
   - 7.5 [News Data](#75-news-data)  
8. [LLM Client Layer (`llm_clients/`)](#8-llm-client-layer-llm_clients)  
9. [Graph Engine (`graph/`)](#9-graph-engine-graph)  
   - 9.1 [Graph Setup & Wiring](#91-graph-setup--wiring)  
   - 9.2 [Conditional Logic / Routing](#92-conditional-logic--routing)  
   - 9.3 [Propagation](#93-propagation)  
   - 9.4 [Reflection & Memory](#94-reflection--memory)  
   - 9.5 [Signal Processing](#95-signal-processing)  
10. [Memory System](#10-memory-system)  
11. [Tool Definitions](#11-tool-definitions)  
12. [CLI Application (`cli/`)](#12-cli-application-cli)  
13. [Configuration Reference](#13-configuration-reference)  
14. [Key Dependencies](#14-key-dependencies)  
15. [Entrypoints](#15-entrypoints)  
16. [Extending the Framework — Integration Guide](#16-extending-the-framework--integration-guide)  
17. [API Quick-Reference for Reuse](#17-api-quick-reference-for-reuse)  

---

## 1. Executive Overview

**TradingAgents** is a multi-agent, LLM-powered algorithmic trading research framework that mirrors the organizational structure of a real-world trading firm. It decomposes the trading decision pipeline into specialized roles — analysts, researchers, a trader, risk managers, and a portfolio manager — each implemented as an autonomous LLM agent. These agents collaborate through structured debates and sequential workflows, producing a final actionable trade signal (`BUY`, `OVERWEIGHT`, `HOLD`, `UNDERWEIGHT`, or `SELL`).

### Key Capabilities

| Capability | Detail |
|---|---|
| **Multi-agent debate architecture** | Bull/Bear researcher debates + Aggressive/Conservative/Neutral risk debates |
| **Multi-provider LLM support** | OpenAI (GPT-5.x), Google (Gemini 3.x), Anthropic (Claude 4.x), xAI (Grok 4.x), OpenRouter, Ollama |
| **Dual-LLM strategy** | Separate "quick-think" (analysts, researchers) and "deep-think" (managers, judges) models |
| **Multi-vendor data** | yfinance (free, default) and Alpha Vantage with automatic failover |
| **Reflection & learning** | Post-trade reflection updates BM25-based memory for future decisions |
| **Five-tier rating scale** | BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL |
| **Rich CLI** | Interactive terminal UI with real-time progress, agent status, and report display |
| **International ticker support** | Preserves exchange suffixes (`.TO`, `.L`, `.HK`, `.T`) throughout the pipeline |

---

## 2. Architecture at a Glance

```
┌──────────────────────────────────────────────────────────────────────┐
│                          TradingAgentsGraph                          │
│                        (LangGraph StateGraph)                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐ │
│   │   Market     │  │   Social    │  │   News   │  │ Fundamentals │ │
│   │   Analyst    │  │   Analyst   │  │  Analyst │  │   Analyst    │ │
│   └──────┬──────┘  └──────┬──────┘  └────┬─────┘  └──────┬───────┘ │
│          │                │               │               │         │
│          └────────────────┴───────┬───────┴───────────────┘         │
│                                   ▼                                  │
│                    ┌──────────────────────────┐                      │
│                    │    RESEARCHER DEBATE      │                      │
│                    │  Bull ←→ Bear (N rounds)  │                      │
│                    └────────────┬─────────────┘                      │
│                                 ▼                                    │
│                    ┌──────────────────────────┐                      │
│                    │    Research Manager       │                      │
│                    │    (Investment Judge)     │                      │
│                    └────────────┬─────────────┘                      │
│                                 ▼                                    │
│                    ┌──────────────────────────┐                      │
│                    │        Trader             │                      │
│                    └────────────┬─────────────┘                      │
│                                 ▼                                    │
│                    ┌──────────────────────────┐                      │
│                    │     RISK DEBATE           │                      │
│                    │ Aggressive ←→ Conserv.    │                      │
│                    │      ←→ Neutral (N rnds)  │                      │
│                    └────────────┬─────────────┘                      │
│                                 ▼                                    │
│                    ┌──────────────────────────┐                      │
│                    │   Portfolio Manager       │                      │
│                    │   (Final Decision)        │                      │
│                    └──────────────────────────┘                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
         │                        │                         │
    ┌────▼─────┐          ┌──────▼──────┐           ┌──────▼──────┐
    │ Data     │          │  LLM Client │           │   Memory    │
    │ Layer    │          │  Factory    │           │   (BM25)    │
    │ yfinance │          │  OpenAI /   │           │             │
    │ AlphaV.  │          │  Anthropic/ │           │             │
    └──────────┘          │  Google/xAI │           └─────────────┘
                          └─────────────┘
```

---

## 3. Directory Structure

```
tradingagents/                    # Core framework package
├── __init__.py                   # Sets PYTHONUTF8=1
├── default_config.py             # DEFAULT_CONFIG dictionary
├── agents/                       # All agent implementations
│   ├── analysts/                 #   Market, Social, News, Fundamentals
│   ├── researchers/              #   Bull & Bear researchers
│   ├── managers/                 #   Research Manager & Portfolio Manager
│   ├── risk_mgmt/                #   Aggressive, Conservative, Neutral debators
│   ├── trader/                   #   Trader agent
│   └── utils/                    #   States, tools, memory, utilities
├── dataflows/                    # Data acquisition & vendor routing
│   ├── interface.py              #   Vendor router (route_to_vendor)
│   ├── config.py                 #   Runtime config singleton
│   ├── y_finance.py              #   yfinance: OHLCV, indicators, fundamentals
│   ├── yfinance_news.py          #   yfinance: news via Ticker.get_news & Search
│   ├── stockstats_utils.py       #   stockstats wrapper + yf_retry
│   ├── alpha_vantage.py          #   Alpha Vantage re-exports
│   ├── alpha_vantage_common.py   #   AV API client, rate-limit handling
│   ├── alpha_vantage_stock.py    #   AV daily adjusted OHLCV
│   ├── alpha_vantage_indicator.py#   AV technical indicators
│   ├── alpha_vantage_fundamentals.py # AV company overview, statements
│   ├── alpha_vantage_news.py     #   AV news sentiment
│   └── utils.py                  #   Date helpers, save utilities
├── graph/                        # LangGraph orchestration
│   ├── trading_graph.py          #   TradingAgentsGraph main class
│   ├── setup.py                  #   GraphSetup — wires the StateGraph
│   ├── propagation.py            #   Propagator — initial state & args
│   ├── conditional_logic.py      #   Routing: debate loops, tool calls
│   ├── reflection.py             #   Post-trade reflection engine
│   └── signal_processing.py      #   Extracts BUY/HOLD/SELL from text
└── llm_clients/                  # LLM provider abstraction
    ├── base_client.py            #   ABC + content normalization
    ├── factory.py                #   create_llm_client()
    ├── openai_client.py          #   OpenAI/Ollama/OpenRouter/xAI
    ├── anthropic_client.py       #   Anthropic Claude
    ├── google_client.py          #   Google Gemini
    └── validators.py             #   Model name validation

cli/                              # Interactive CLI application
├── main.py                       #   Typer app, Rich live display, streaming
├── utils.py                      #   Questionary prompts, provider/model selection
├── models.py                     #   AnalystType enum
├── config.py                     #   CLI_CONFIG (announcements URL)
├── announcements.py              #   Remote announcements fetcher
├── stats_handler.py              #   LangChain callback for LLM/tool/token stats
└── static/welcome.txt            #   ASCII art banner

tests/
└── test_ticker_symbol_handling.py # Ticker normalization + context tests
```

---

## 4. Core Pipeline & Execution Flow

The entire pipeline is executed via `TradingAgentsGraph.propagate(ticker, date)`:

```
1. INITIALIZATION
   └─ Propagator.create_initial_state(ticker, date)
        → AgentState with empty reports, empty debate states

2. ANALYST PHASE (sequential, tool-calling loop per analyst)
   ├─ Market Analyst    → calls get_stock_data, get_indicators → market_report
   ├─ Social Analyst    → calls get_news                       → sentiment_report
   ├─ News Analyst      → calls get_news, get_global_news      → news_report
   └─ Fundamentals Analyst → calls get_fundamentals, get_balance_sheet,
                              get_cashflow, get_income_statement → fundamentals_report

3. RESEARCHER DEBATE PHASE (configurable rounds)
   ├─ Bull Researcher argues FOR investment (uses memory)
   ├─ Bear Researcher argues AGAINST investment (uses memory)
   └─ Alternating for `max_debate_rounds` × 2 iterations
   
4. RESEARCH MANAGER JUDGMENT
   └─ Evaluates debate → investment_plan (Buy/Sell/Hold + rationale)

5. TRADER PHASE
   └─ Synthesizes all reports + investment_plan → trader_investment_plan

6. RISK DEBATE PHASE (configurable rounds)
   ├─ Aggressive Analyst  → champions high-risk/high-reward
   ├─ Conservative Analyst → prioritizes asset protection
   ├─ Neutral Analyst      → balanced perspective
   └─ Rotating for `max_risk_discuss_rounds` × 3 iterations

7. PORTFOLIO MANAGER (FINAL DECISION)
   └─ Synthesizes risk debate → final_trade_decision
       Rating: BUY | OVERWEIGHT | HOLD | UNDERWEIGHT | SELL

8. SIGNAL PROCESSING
   └─ SignalProcessor extracts single-word rating from full text

9. OPTIONAL: REFLECTION
   └─ reflect_and_remember(returns) → updates 5 memory stores
```

---

## 5. Agent Taxonomy (All Agents)

### 5.1 Analyst Team

Each analyst is a tool-calling LLM agent that loops until all needed data is gathered, then writes a comprehensive Markdown report with an appended summary table.

| Agent | File | Tools Used | Output State Key | Purpose |
|---|---|---|---|---|
| **Market Analyst** | `analysts/market_analyst.py` | `get_stock_data`, `get_indicators` | `market_report` | Technical analysis: OHLCV data + up to 8 indicators (SMA, EMA, MACD, RSI, Bollinger, ATR, VWMA, MFI) |
| **Social Media Analyst** | `analysts/social_media_analyst.py` | `get_news` | `sentiment_report` | Public sentiment, social media discussions, company-specific news sentiment |
| **News Analyst** | `analysts/news_analyst.py` | `get_news`, `get_global_news` | `news_report` | Macro-economic news, global market events, company-specific news |
| **Fundamentals Analyst** | `analysts/fundamentals_analyst.py` | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` | `fundamentals_report` | Financial statements, company profile, key ratios, valuation metrics |

**Analyst Prompt Pattern:** Each analyst uses a `ChatPromptTemplate` with a collaborative system prompt, tool binding via `llm.bind_tools(tools)`, and conditional looping (if the LLM returns tool calls, the tools execute and loop back; otherwise, the report text is captured).

### 5.2 Researcher Team

| Agent | File | Role | Memory Used |
|---|---|---|---|
| **Bull Researcher** | `researchers/bull_researcher.py` | Advocates FOR the investment. Focuses on growth potential, competitive advantages, positive indicators. Counters Bear arguments. | `bull_memory` |
| **Bear Researcher** | `researchers/bear_researcher.py` | Advocates AGAINST the investment. Focuses on risks, competitive weaknesses, negative indicators. Counters Bull arguments. | `bear_memory` |
| **Research Manager** | `managers/research_manager.py` | Judges the Bull/Bear debate. Makes a decisive recommendation (Buy/Sell/Hold) with a detailed investment plan. Uses deep-thinking LLM. | `invest_judge_memory` |

**Debate Mechanics:** Bull and Bear alternate for `max_debate_rounds * 2` total turns. Each sees the full debate history, all analyst reports, and relevant past memories. The Research Manager then synthesizes the debate into an `investment_plan`.

### 5.3 Trader Agent

| Agent | File | Role | Memory Used |
|---|---|---|---|
| **Trader** | `trader/trader.py` | Converts the investment plan into a concrete trading proposal (BUY/HOLD/SELL). Uses all analyst reports + past trade reflections. | `trader_memory` |

### 5.4 Risk Management Team

| Agent | File | Perspective |
|---|---|---|
| **Aggressive Analyst** | `risk_mgmt/aggressive_debator.py` | Champions high-reward, high-risk opportunities. Counters conservative/neutral caution. |
| **Conservative Analyst** | `risk_mgmt/conservative_debator.py` | Prioritizes asset protection, stability, risk minimization. Counters aggressive optimism. |
| **Neutral Analyst** | `risk_mgmt/neutral_debator.py` | Balanced view. Challenges both extremes for a moderate, sustainable strategy. |

**Risk Debate Mechanics:** Aggressive → Conservative → Neutral rotation for `max_risk_discuss_rounds * 3` total turns. Each agent sees the trader's proposal, all analyst reports, and the full risk debate history.

### 5.5 Portfolio Manager

| Agent | File | Role | Memory Used |
|---|---|---|---|
| **Portfolio Manager** | `managers/portfolio_manager.py` | Final decision maker. Synthesizes the risk debate into a rating (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL) with executive summary, investment thesis, and strategic actions. Uses deep-thinking LLM. | `portfolio_manager_memory` |

---

## 6. State Management & Data Model

Defined in `agents/utils/agent_states.py` using LangGraph's `TypedDict` pattern:

### `AgentState` (extends `MessagesState`)

| Field | Type | Description |
|---|---|---|
| `messages` | `list[BaseMessage]` | LangGraph message history (auto-managed) |
| `company_of_interest` | `str` | Ticker symbol being analyzed |
| `trade_date` | `str` | Analysis date (YYYY-MM-DD) |
| `sender` | `str` | Agent that sent the last message |
| `market_report` | `str` | Output from Market Analyst |
| `sentiment_report` | `str` | Output from Social Media Analyst |
| `news_report` | `str` | Output from News Analyst |
| `fundamentals_report` | `str` | Output from Fundamentals Analyst |
| `investment_debate_state` | `InvestDebateState` | Bull/Bear debate state |
| `investment_plan` | `str` | Research Manager's plan |
| `trader_investment_plan` | `str` | Trader's concrete proposal |
| `risk_debate_state` | `RiskDebateState` | Risk team debate state |
| `final_trade_decision` | `str` | Portfolio Manager's final decision |

### `InvestDebateState`

| Field | Type | Description |
|---|---|---|
| `bull_history` | `str` | Accumulated Bull arguments |
| `bear_history` | `str` | Accumulated Bear arguments |
| `history` | `str` | Combined debate transcript |
| `current_response` | `str` | Latest argument (prefixed "Bull Analyst:" or "Bear Analyst:") |
| `judge_decision` | `str` | Research Manager's ruling |
| `count` | `int` | Turn counter (controls debate termination) |

### `RiskDebateState`

| Field | Type | Description |
|---|---|---|
| `aggressive_history` | `str` | Accumulated Aggressive arguments |
| `conservative_history` | `str` | Accumulated Conservative arguments |
| `neutral_history` | `str` | Accumulated Neutral arguments |
| `history` | `str` | Combined debate transcript |
| `latest_speaker` | `str` | Determines next speaker in rotation |
| `current_aggressive_response` | `str` | Latest Aggressive argument |
| `current_conservative_response` | `str` | Latest Conservative argument |
| `current_neutral_response` | `str` | Latest Neutral argument |
| `judge_decision` | `str` | Portfolio Manager's ruling |
| `count` | `int` | Turn counter |

---

## 7. Data Layer (`dataflows/`)

### 7.1 Vendor Abstraction & Routing

**File:** `interface.py`

The data layer uses a **vendor-agnostic routing pattern**. Every tool calls `route_to_vendor(method_name, *args)`, which:

1. Looks up the **category** for the method (e.g., `get_stock_data` → `core_stock_apis`)
2. Checks **tool-level overrides** (`config["tool_vendors"]`) first
3. Falls back to **category-level config** (`config["data_vendors"]`)
4. Resolves the vendor to a concrete function via `VENDOR_METHODS` dispatch table
5. Executes with **automatic failover** — if Alpha Vantage rate-limits (`AlphaVantageRateLimitError`), falls back to the next available vendor

**Tool Categories:**

| Category | Tools | Vendors |
|---|---|---|
| `core_stock_apis` | `get_stock_data` | yfinance, alpha_vantage |
| `technical_indicators` | `get_indicators` | yfinance, alpha_vantage |
| `fundamental_data` | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` | yfinance, alpha_vantage |
| `news_data` | `get_news`, `get_global_news`, `get_insider_transactions` | yfinance, alpha_vantage |

### 7.2 yfinance Provider

**Files:** `y_finance.py`, `stockstats_utils.py`

| Function | Description |
|---|---|
| `get_YFin_data_online(symbol, start, end)` | OHLCV data via `yf.Ticker.history()` → CSV string |
| `get_stock_stats_indicators_window(symbol, indicator, date, lookback)` | Technical indicator via `stockstats` library. Bulk computation with caching. |
| `get_fundamentals(ticker)` | Company info: PE, EPS, margins, revenue, etc. via `yf.Ticker.info` |
| `get_balance_sheet(ticker, freq)` | Balance sheet (quarterly/annual) |
| `get_cashflow(ticker, freq)` | Cash flow statement |
| `get_income_statement(ticker, freq)` | Income statement |
| `get_insider_transactions(ticker)` | Insider transactions |

**Caching:** Stock data for indicator calculations is cached to CSV files at `data_cache_dir` with filenames like `{symbol}-YFin-data-{start}-{end}.csv`. Data spans 15 years from today.

**Rate Limit Handling:** `yf_retry()` wraps all yfinance calls with exponential backoff (up to 3 retries) on `YFRateLimitError`.

**Supported Technical Indicators:**

| Indicator Key | Description |
|---|---|
| `close_50_sma` | 50-period Simple Moving Average |
| `close_200_sma` | 200-period Simple Moving Average |
| `close_10_ema` | 10-period Exponential Moving Average |
| `macd` | MACD line |
| `macds` | MACD Signal line |
| `macdh` | MACD Histogram |
| `rsi` | Relative Strength Index |
| `boll` | Bollinger Middle Band (20 SMA) |
| `boll_ub` | Bollinger Upper Band |
| `boll_lb` | Bollinger Lower Band |
| `atr` | Average True Range |
| `vwma` | Volume Weighted Moving Average |
| `mfi` | Money Flow Index |

### 7.3 Alpha Vantage Provider

**Files:** `alpha_vantage_common.py`, `alpha_vantage_stock.py`, `alpha_vantage_indicator.py`, `alpha_vantage_fundamentals.py`, `alpha_vantage_news.py`

| Function | AV Endpoint | Notes |
|---|---|---|
| `get_stock(symbol, start, end)` | `TIME_SERIES_DAILY_ADJUSTED` | Auto-selects `compact`/`full` based on date range |
| `get_indicator(symbol, ind, date, lookback)` | Various (`SMA`, `EMA`, `MACD`, `RSI`, `BBANDS`, `ATR`) | Maps internal indicator keys to AV API functions |
| `get_fundamentals(ticker)` | `OVERVIEW` | Company overview with financial ratios |
| `get_balance_sheet(ticker)` | `BALANCE_SHEET` | |
| `get_cashflow(ticker)` | `CASH_FLOW` | |
| `get_income_statement(ticker)` | `INCOME_STATEMENT` | |
| `get_news(ticker, start, end)` | `NEWS_SENTIMENT` | News sentiment for specific ticker |
| `get_global_news(date, lookback, limit)` | `NEWS_SENTIMENT` | Global macro news (topics: financial_markets, economy) |
| `get_insider_transactions(symbol)` | `INSIDER_TRANSACTIONS` | |

**Rate Limit Handling:** `AlphaVantageRateLimitError` is raised on API rate limits or key issues. The router catches this and falls back to yfinance.

### 7.4 Technical Indicators

The `stockstats` library is used for all yfinance-based indicator calculations. The `_get_stock_stats_bulk()` function computes indicators for the entire dataset at once (optimized), with a fallback to per-date calculation via `StockstatsUtils.get_stock_stats()`.

### 7.5 News Data

**File:** `yfinance_news.py`

| Function | Description |
|---|---|
| `get_news_yfinance(ticker, start, end)` | Ticker-specific news via `yf.Ticker.get_news()` with date filtering |
| `get_global_news_yfinance(date, lookback, limit)` | Global news via `yf.Search()` across multiple macro queries with deduplication |

News article parsing handles both flat and nested (`content` key) structures from yfinance, extracting title, summary, publisher, URL, and publication date.

---

## 8. LLM Client Layer (`llm_clients/`)

### Factory Pattern

```python
client = create_llm_client(provider="openai", model="gpt-5-mini", **kwargs)
llm = client.get_llm()  # Returns a LangChain chat model
```

### Provider Implementations

| Provider | Client Class | LangChain Wrapper | Key Features |
|---|---|---|---|
| **OpenAI** | `OpenAIClient` | `NormalizedChatOpenAI` | Uses Responses API (`use_responses_api=True`), supports `reasoning_effort` |
| **Anthropic** | `AnthropicClient` | `NormalizedChatAnthropic` | Supports `effort` parameter for Claude 4.5+/4.6 |
| **Google** | `GoogleClient` | `NormalizedChatGoogleGenerativeAI` | Maps `thinking_level` to Gemini 3 API params or `thinking_budget` for 2.5 |
| **xAI** | `OpenAIClient` (reused) | Same as OpenAI | Base URL: `https://api.x.ai/v1` |
| **OpenRouter** | `OpenAIClient` (reused) | Same as OpenAI | Base URL: `https://openrouter.ai/api/v1` |
| **Ollama** | `OpenAIClient` (reused) | Same as OpenAI | Base URL: `http://localhost:11434/v1`, API key: `"ollama"` |

### Content Normalization

All provider wrappers include `normalize_content()` which converts list-based content responses (from Responses API, extended thinking, etc.) into plain strings. This ensures all downstream agents receive consistent `response.content` as a string.

### Supported Models (as of v0.2.2)

| Provider | Models |
|---|---|
| **OpenAI** | gpt-5.4-pro, gpt-5.4, gpt-5.2, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano |
| **Anthropic** | claude-opus-4-6, claude-sonnet-4-6, claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5 |
| **Google** | gemini-3.1-pro-preview, gemini-3.1-flash-lite-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite |
| **xAI** | grok-4-1-fast-reasoning, grok-4-1-fast-non-reasoning, grok-4-0709, grok-4-fast-reasoning, grok-4-fast-non-reasoning |
| **Ollama/OpenRouter** | Any model (no validation) |

---

## 9. Graph Engine (`graph/`)

### 9.1 Graph Setup & Wiring

**File:** `setup.py` — `GraphSetup.setup_graph(selected_analysts)`

Constructs a `langgraph.StateGraph(AgentState)` with:

- **Analyst nodes:** One per selected analyst, each with a paired tool node and message-clear node
- **Sequential analyst flow:** Analysts execute in order (market → social → news → fundamentals), each looping with tools until complete
- **Message clearing:** Between analysts, messages are cleared (with a "Continue" placeholder for Anthropic compatibility)
- **Debate nodes:** Bull/Bear researchers with conditional back-and-forth
- **Risk debate nodes:** Aggressive/Conservative/Neutral with rotating conditional edges
- **Terminal node:** Portfolio Manager → `END`

### 9.2 Conditional Logic / Routing

**File:** `conditional_logic.py`

| Method | Logic |
|---|---|
| `should_continue_{market,social,news,fundamentals}` | If last message has `tool_calls` → route to tools; else → route to Msg Clear |
| `should_continue_debate` | If `count >= 2 * max_debate_rounds` → Research Manager; else alternate Bull/Bear |
| `should_continue_risk_analysis` | If `count >= 3 * max_risk_discuss_rounds` → Portfolio Manager; else rotate Aggressive → Conservative → Neutral |

### 9.3 Propagation

**File:** `propagation.py`

`Propagator.create_initial_state()` builds the complete initial `AgentState` with empty reports, zeroed debate states, and the ticker/date. `get_graph_args()` returns stream config with recursion limit.

### 9.4 Reflection & Memory

**File:** `reflection.py`

After a trade, `reflect_and_remember(returns_losses)` triggers reflection for **all 5 memory-equipped agents**:

1. Bull Researcher
2. Bear Researcher
3. Trader
4. Investment Judge (Research Manager)
5. Portfolio Manager

Each reflection:
- Assembles the current market situation from all 4 reports
- Sends the agent's original analysis + actual returns to the LLM
- Receives a detailed reflection (reasoning, improvements, lessons, condensed query)
- Stores the (situation, reflection) pair in the agent's BM25 memory

### 9.5 Signal Processing

**File:** `signal_processing.py`

`SignalProcessor.process_signal(full_signal)` uses a quick-thinking LLM to extract exactly one word from: `BUY`, `OVERWEIGHT`, `HOLD`, `UNDERWEIGHT`, `SELL`.

---

## 10. Memory System

**File:** `agents/utils/memory.py` — `FinancialSituationMemory`

A **BM25-based lexical similarity** memory system. Fully offline, no API calls, no token limits.

| Method | Description |
|---|---|
| `add_situations([(situation, recommendation), ...])` | Store situation-recommendation pairs and rebuild BM25 index |
| `get_memories(current_situation, n_matches)` | Retrieve top-N most similar past situations with their recommendations |
| `clear()` | Reset all memories |

**Tokenization:** Simple whitespace + punctuation splitting with lowercasing.  
**Scoring:** BM25Okapi scores normalized to 0–1 range.  
**Usage:** Each memory-equipped agent retrieves `n_matches=2` past reflections for similar market situations and includes them in their prompts.

---

## 11. Tool Definitions

All tools are defined as `@tool`-decorated functions (LangChain tools) in `agents/utils/`:

| File | Tool Functions | Category |
|---|---|---|
| `core_stock_tools.py` | `get_stock_data(symbol, start_date, end_date)` | `core_stock_apis` |
| `technical_indicators_tools.py` | `get_indicators(symbol, indicator, curr_date, look_back_days)` | `technical_indicators` |
| `fundamental_data_tools.py` | `get_fundamentals(ticker, curr_date)`, `get_balance_sheet(ticker, freq, curr_date)`, `get_cashflow(ticker, freq, curr_date)`, `get_income_statement(ticker, freq, curr_date)` | `fundamental_data` |
| `news_data_tools.py` | `get_news(ticker, start_date, end_date)`, `get_global_news(curr_date, look_back_days, limit)`, `get_insider_transactions(ticker)` | `news_data` |

All tools internally call `route_to_vendor()` which resolves to the configured data provider. The `get_indicators` tool also handles comma-separated indicator lists by splitting and processing individually.

**Tool Node Mapping:**

| ToolNode Key | Assigned To | Tools |
|---|---|---|
| `market` | Market Analyst | `get_stock_data`, `get_indicators` |
| `social` | Social Media Analyst | `get_news` |
| `news` | News Analyst | `get_news`, `get_global_news`, `get_insider_transactions` |
| `fundamentals` | Fundamentals Analyst | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` |

---

## 12. CLI Application (`cli/`)

### Overview

The CLI is built with **Typer** (command framework), **Rich** (terminal UI), and **Questionary** (interactive prompts).

### User Flow

1. **Welcome screen** — ASCII art banner + announcements from remote endpoint
2. **Ticker selection** — Free-text input with exchange-suffix preservation
3. **Date selection** — YYYY-MM-DD validated, cannot be future
4. **Analyst selection** — Checkbox multi-select (Market, Social, News, Fundamentals)
5. **Research depth** — Shallow (1) / Medium (3) / Deep (5) debate rounds
6. **LLM provider** — OpenAI / Google / Anthropic / xAI / OpenRouter / Ollama
7. **Model selection** — Quick-think and Deep-think models (provider-specific lists)
8. **Provider-specific config** — Reasoning effort (OpenAI), thinking level (Google), effort (Anthropic)
9. **Live analysis** — Rich `Live` display with:
   - Agent progress table (pending/in_progress/completed per agent)
   - Messages & tool calls log (newest first)
   - Current report panel (Markdown rendered)
   - Footer stats (agents, LLM calls, tool calls, tokens, elapsed time)
10. **Post-analysis** — Save report to disk (organized subfolders) + display full report

### Stats Tracking

**File:** `stats_handler.py` — `StatsCallbackHandler`

A LangChain `BaseCallbackHandler` that tracks:
- LLM call count (via `on_llm_start` / `on_chat_model_start`)
- Tool call count (via `on_tool_start`)
- Token usage (via `on_llm_end` → `usage_metadata`)
- Thread-safe with `threading.Lock`

### Report Saving

Reports are saved to organized subfolders:
```
reports/{ticker}_{timestamp}/
├── complete_report.md            # Consolidated report
├── 1_analysts/
│   ├── market.md
│   ├── sentiment.md
│   ├── news.md
│   └── fundamentals.md
├── 2_research/
│   ├── bull.md
│   ├── bear.md
│   └── manager.md
├── 3_trading/
│   └── trader.md
├── 4_risk/
│   ├── aggressive.md
│   ├── conservative.md
│   └── neutral.md
└── 5_portfolio/
    └── decision.md
```

---

## 13. Configuration Reference

**File:** `default_config.py`

```python
DEFAULT_CONFIG = {
    # Directories
    "project_dir": "<auto>",                    # Package root
    "results_dir": "./results",                 # CLI output directory
    "data_cache_dir": "<project_dir>/dataflows/data_cache",

    # LLM Settings
    "llm_provider": "openai",                   # openai|google|anthropic|xai|openrouter|ollama
    "deep_think_llm": "gpt-5.2",               # Model for managers/judges
    "quick_think_llm": "gpt-5-mini",            # Model for analysts/researchers
    "backend_url": "https://api.openai.com/v1", # API base URL

    # Provider-Specific Thinking
    "google_thinking_level": None,              # "high", "minimal", etc.
    "openai_reasoning_effort": None,            # "medium", "high", "low"
    "anthropic_effort": None,                   # "high", "medium", "low"

    # Debate Settings
    "max_debate_rounds": 1,                     # Bull/Bear rounds (total turns = 2×)
    "max_risk_discuss_rounds": 1,               # Risk debate rounds (total turns = 3×)
    "max_recur_limit": 100,                     # LangGraph recursion limit

    # Data Vendor Configuration (category-level)
    "data_vendors": {
        "core_stock_apis": "yfinance",          # yfinance | alpha_vantage
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    },

    # Tool-Level Overrides (takes precedence)
    "tool_vendors": {},                         # e.g., {"get_stock_data": "alpha_vantage"}
}
```

---

## 14. Key Dependencies

| Package | Purpose |
|---|---|
| `langgraph` ≥ 0.4.8 | Agent graph orchestration |
| `langchain-core` ≥ 0.3.81 | Tool definitions, message types, callbacks |
| `langchain-openai` ≥ 0.3.23 | OpenAI/compatible LLM clients |
| `langchain-anthropic` ≥ 0.3.15 | Anthropic Claude clients |
| `langchain-google-genai` ≥ 2.1.5 | Google Gemini clients |
| `yfinance` ≥ 0.2.63 | Stock data, fundamentals, news |
| `stockstats` ≥ 0.6.5 | Technical indicator calculations |
| `rank-bm25` ≥ 0.2.2 | Memory retrieval (BM25 algorithm) |
| `pandas` ≥ 2.3.0 | Data manipulation |
| `rich` ≥ 14.0.0 | CLI terminal rendering |
| `typer` ≥ 0.21.0 | CLI command framework |
| `questionary` ≥ 2.1.0 | Interactive prompts |
| `requests` ≥ 2.32.4 | HTTP for Alpha Vantage API |
| `redis` ≥ 6.2.0 | Listed dependency (not actively used in current code) |
| `backtrader` ≥ 1.9.78 | Listed dependency (backtesting support) |

---

## 15. Entrypoints

| Method | Description |
|---|---|
| `tradingagents` (CLI) | Interactive terminal application → `cli.main:app` |
| `python -m cli.main` | Alternative CLI launch |
| `python main.py` | Programmatic usage example |
| **Programmatic API:** | |
| `TradingAgentsGraph(config=...).propagate(ticker, date)` | Returns `(final_state, decision)` |
| `graph.reflect_and_remember(returns)` | Post-trade learning |

---

## 16. Extending the Framework — Integration Guide

### Adding a New Data Vendor

1. Create `dataflows/new_vendor.py` with functions matching the signatures in `VENDOR_METHODS`
2. Add vendor to `VENDOR_METHODS` dict in `interface.py`
3. Add vendor name to `VENDOR_LIST` in `interface.py`
4. Configure via `config["data_vendors"]` or `config["tool_vendors"]`

### Adding a New LLM Provider

1. Create `llm_clients/new_provider_client.py` extending `BaseLLMClient`
2. Implement `get_llm()` → return a LangChain-compatible chat model
3. Register in `factory.py`'s `create_llm_client()` dispatch
4. Add valid model names to `validators.py`

### Adding a New Analyst

1. Create `agents/analysts/new_analyst.py` with `create_new_analyst(llm)` function
2. Define new tools in `agents/utils/` if needed
3. Register tool node in `TradingAgentsGraph._create_tool_nodes()`
4. Add to `GraphSetup.setup_graph()` logic
5. Add corresponding state field in `AgentState`
6. Update `ConditionalLogic` with `should_continue_new_analyst()`

### Adding a New Technical Indicator

1. Add indicator key + description to `best_ind_params` dict in `y_finance.py`
2. If using Alpha Vantage, add API mapping in `alpha_vantage_indicator.py`
3. The indicator name must be a valid `stockstats` column accessor

### Using Individual Components

The framework is modular. You can reuse individual pieces:

```python
# Just the data layer
from tradingagents.dataflows.y_finance import get_YFin_data_online, get_stock_stats_indicators_window
from tradingagents.dataflows.yfinance_news import get_news_yfinance

# Just the memory system
from tradingagents.agents.utils.memory import FinancialSituationMemory

# Just the LLM factory
from tradingagents.llm_clients import create_llm_client

# Just the vendor routing
from tradingagents.dataflows.interface import route_to_vendor
```

---

## 17. API Quick-Reference for Reuse

### Data Functions (Direct, No LLM Required)

```python
# Stock OHLCV data
from tradingagents.dataflows.y_finance import get_YFin_data_online
csv_data = get_YFin_data_online("AAPL", "2024-01-01", "2024-12-31")

# Technical indicators (single indicator, windowed)
from tradingagents.dataflows.y_finance import get_stock_stats_indicators_window
rsi = get_stock_stats_indicators_window("AAPL", "rsi", "2024-12-01", 30)

# Company fundamentals
from tradingagents.dataflows.y_finance import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement
info = get_fundamentals("AAPL")
bs = get_balance_sheet("AAPL", freq="quarterly")
cf = get_cashflow("AAPL", freq="annual")
inc = get_income_statement("AAPL")

# Insider transactions
from tradingagents.dataflows.y_finance import get_insider_transactions
insiders = get_insider_transactions("AAPL")

# Ticker-specific news
from tradingagents.dataflows.yfinance_news import get_news_yfinance
news = get_news_yfinance("AAPL", "2024-11-01", "2024-12-01")

# Global/macro news
from tradingagents.dataflows.yfinance_news import get_global_news_yfinance
global_news = get_global_news_yfinance("2024-12-01", look_back_days=7, limit=10)

# Vendor-routed (respects config)
from tradingagents.dataflows.interface import route_to_vendor
data = route_to_vendor("get_stock_data", "AAPL", "2024-01-01", "2024-12-31")
```

### Full Pipeline

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["quick_think_llm"] = "gpt-5-mini"
config["deep_think_llm"] = "gpt-5.2"
config["max_debate_rounds"] = 2

ta = TradingAgentsGraph(
    selected_analysts=["market", "news", "fundamentals"],
    debug=True,
    config=config,
)

final_state, decision = ta.propagate("NVDA", "2024-05-10")
# decision: "BUY" | "OVERWEIGHT" | "HOLD" | "UNDERWEIGHT" | "SELL"

# Post-trade reflection (optional)
ta.reflect_and_remember(returns_losses=1500)  # positive = profit
```

### Memory System (Standalone)

```python
from tradingagents.agents.utils.memory import FinancialSituationMemory

memory = FinancialSituationMemory("my_strategy_memory")
memory.add_situations([
    ("High RSI with declining volume in tech sector", "Reduce position, watch for reversal"),
    ("Strong earnings beat with institutional buying", "Add to position on pullback"),
])

matches = memory.get_memories("RSI above 70, tech stocks, volume dropping", n_matches=2)
for m in matches:
    print(f"Score: {m['similarity_score']:.2f} → {m['recommendation']}")
```

---

*This summary covers every module, class, function, and data flow in the TradingAgents v0.2.2 codebase. It is intended as a comprehensive reference for evaluating, integrating, or extending components into your own algorithmic trading project.*
