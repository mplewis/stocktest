# Stocktest Application Workflow

This document visualizes the execution flow of the stocktest application, highlighting parallel vs serial execution.

## High-Level Execution Flow

```mermaid
flowchart TD
    Start([User runs stocktest]) --> CLI[CLI Entry Point]
    CLI --> LoadConfig[Load YAML Configuration]
    LoadConfig --> ValidateConfig[Validate Config]
    ValidateConfig --> SelectPeriod[Select Period to Run]
    SelectPeriod --> PeriodLoop{For Each Period}

    PeriodLoop --> PreFetch[Pre-fetch All Tickers<br/>PARALLEL]
    PreFetch --> RunBacktests[Run All Backtests<br/>PARALLEL]

    RunBacktests --> GenerateReports[Generate Reports<br/>SERIAL]
    GenerateReports --> PeriodLoop

    PeriodLoop --> End([Complete])

    style PreFetch fill:#90EE90
    style RunBacktests fill:#90EE90
    style GenerateReports fill:#FFB6C1
```

## Detailed Data Fetching Flow (Parallel Execution)

```mermaid
flowchart TD
    Start([fetch_multiple_tickers called]) --> CreateSemaphore[Create Semaphore<br/>max_concurrent=5]
    CreateSemaphore --> CreateTasks[Create async tasks<br/>for all tickers]
    CreateTasks --> AsyncGather[asyncio.gather - Execute in Parallel]

    AsyncGather --> T1[Ticker 1<br/>fetch_ticker_async]
    AsyncGather --> T2[Ticker 2<br/>fetch_ticker_async]
    AsyncGather --> T3[Ticker 3<br/>fetch_ticker_async]
    AsyncGather --> T4[Ticker 4<br/>fetch_ticker_async]
    AsyncGather --> T5[Ticker 5<br/>fetch_ticker_async]
    AsyncGather --> TN[...more tickers<br/>queued]

    T1 --> Sem1{Acquire Semaphore}
    T2 --> Sem2{Acquire Semaphore}
    T3 --> Sem3{Acquire Semaphore}
    T4 --> Sem4{Acquire Semaphore}
    T5 --> Sem5{Acquire Semaphore}
    TN --> SemN{Wait for Slot}

    Sem1 --> Fetch1[Check Cache]
    Sem2 --> Fetch2[Check Cache]
    Sem3 --> Fetch3[Check Cache]
    Sem4 --> Fetch4[Check Cache]
    Sem5 --> Fetch5[Check Cache]

    Fetch1 --> API1[API Call if needed]
    Fetch2 --> API2[API Call if needed]
    Fetch3 --> API3[API Call if needed]
    Fetch4 --> API4[API Call if needed]
    Fetch5 --> API5[API Call if needed]

    API1 --> Release1[Release Semaphore<br/>Update Progress]
    API2 --> Release2[Release Semaphore<br/>Update Progress]
    API3 --> Release3[Release Semaphore<br/>Update Progress]
    API4 --> Release4[Release Semaphore<br/>Update Progress]
    API5 --> Release5[Release Semaphore<br/>Update Progress]

    Release1 --> SemN
    Release2 --> SemN
    Release3 --> SemN
    Release4 --> SemN
    Release5 --> SemN

    SemN --> Collect[Collect All Results]
    Collect --> Return([Return dict of DataFrames])

    style AsyncGather fill:#90EE90
    style T1 fill:#90EE90
    style T2 fill:#90EE90
    style T3 fill:#90EE90
    style T4 fill:#90EE90
    style T5 fill:#90EE90
    style TN fill:#FFEB3B
```

## Cache-First Strategy for Individual Ticker

```mermaid
flowchart TD
    Start([fetch_price_data called]) --> CheckNoData{Check no_data_ranges<br/>table}
    CheckNoData -->|Cached as<br/>no-data| RaiseCached[Raise: No data cached]
    CheckNoData -->|Not cached| LoadCache[Load from prices table]

    LoadCache -->|Data exists| FindGaps{Find missing ranges}
    LoadCache -->|No data| FetchNew[Fetch from yfinance]

    FindGaps -->|No gaps| ReturnCached[Return cached data]
    FindGaps -->|Gaps found| FetchGaps[Fetch missing ranges]

    FetchGaps -->|Success| CacheNew1[Cache new data]
    FetchGaps -->|No data| CacheNoData1[Cache no_data_range]

    CacheNew1 --> MergeData[Merge with cached]
    CacheNoData1 --> MergeData
    MergeData --> ReturnMerged[Return merged data]

    FetchNew -->|Success| CacheNew2[Cache price data]
    FetchNew -->|No data| CacheNoData2[Cache no_data_range]

    CacheNew2 --> ReturnNew[Return data]
    CacheNoData2 --> RaiseError[Raise: No data]

    style LoadCache fill:#87CEEB
    style FetchGaps fill:#FFB6C1
    style FetchNew fill:#FFB6C1
```

## Parallel Backtest Execution

```mermaid
flowchart TD
    Start([_run_backtests_parallel called]) --> CreateSemaphore[Create Semaphore<br/>max_concurrent=CPU count]
    CreateSemaphore --> CreateTasks[Create async tasks<br/>for all tickers]
    CreateTasks --> AsyncGather[asyncio.gather - Execute in Parallel]

    AsyncGather --> T1[Ticker 1<br/>_run_backtest_async]
    AsyncGather --> T2[Ticker 2<br/>_run_backtest_async]
    AsyncGather --> T3[Ticker 3<br/>_run_backtest_async]
    AsyncGather --> TN[...more tickers<br/>queued]

    T1 --> Sem1{Acquire Semaphore}
    T2 --> Sem2{Acquire Semaphore}
    T3 --> Sem3{Acquire Semaphore}
    TN --> SemN{Wait for Slot}

    Sem1 --> BT1[Run Backtest +<br/>Calculate Metrics]
    Sem2 --> BT2[Run Backtest +<br/>Calculate Metrics]
    Sem3 --> BT3[Run Backtest +<br/>Calculate Metrics]

    BT1 --> Release1[Release Semaphore<br/>Log Results]
    BT2 --> Release2[Release Semaphore<br/>Log Results]
    BT3 --> Release3[Release Semaphore<br/>Log Results]

    Release1 --> SemN
    Release2 --> SemN
    Release3 --> SemN

    SemN --> Collect[Collect All Results]
    Collect --> Return([Return results & metrics])

    style AsyncGather fill:#90EE90
    style T1 fill:#90EE90
    style T2 fill:#90EE90
    style T3 fill:#90EE90
    style TN fill:#FFEB3B
    style BT1 fill:#90EE90
    style BT2 fill:#90EE90
    style BT3 fill:#90EE90
```

## Individual Backtest Execution (Called by Parallel Executor)

```mermaid
flowchart TD
    Start([run_backtest called]) --> ValidateWeights{Validate weights<br/>sum to 1.0}
    ValidateWeights -->|Invalid| Error[Raise ValueError]
    ValidateWeights -->|Valid| FetchData[Fetch price data<br/>uses cache]

    FetchData --> FilterData[Filter out empty/None<br/>DataFrames]
    FilterData -->|No data| NoDataError[Raise: No data available]
    FilterData -->|Has data| MergeDates[Merge all dates<br/>from all tickers]

    MergeDates --> CalcRebalance[Calculate rebalance dates<br/>daily/weekly/monthly]
    CalcRebalance --> InitPortfolio[Initialize Portfolio<br/>with initial_capital]

    InitPortfolio --> RebalanceLoop{For Each<br/>Rebalance Date}

    RebalanceLoop --> GetPrices[Get current prices<br/>for all tickers]
    GetPrices --> CalcTargets[Calculate target<br/>allocations]
    CalcTargets --> CalcTrades[Calculate required<br/>trades]
    CalcTrades --> ExecTrades[Execute trades<br/>with costs]
    ExecTrades --> RecordState[Record portfolio state]
    RecordState --> RebalanceLoop

    RebalanceLoop --> BuildEquity[Build equity curve<br/>DataFrame]
    BuildEquity --> FetchBenchmark{Benchmark<br/>specified?}

    FetchBenchmark -->|Yes| GetBenchmark[Fetch benchmark data]
    FetchBenchmark -->|No| CalcMetrics[Calculate metrics<br/>without benchmark]

    GetBenchmark --> CalcMetricsB[Calculate metrics<br/>with benchmark]

    CalcMetrics --> Return([Return results dict])
    CalcMetricsB --> Return

    style RebalanceLoop fill:#90EE90
    style GetPrices fill:#90EE90
    style CalcTargets fill:#90EE90
    style ExecTrades fill:#90EE90
```

## Report Generation (Serial)

```mermaid
flowchart TD
    Start([Generate Reports]) --> CreateDirs[Create report directory<br/>structure]
    CreateDirs --> ExportEquity[Export equity_curve.csv]
    ExportEquity --> ExportTrades[Export trade_log.csv]
    ExportTrades --> ExportMetrics[Export summary_stats.csv]
    ExportMetrics --> PlotEquity[Plot equity curve chart]
    PlotEquity --> PlotDrawdown[Plot drawdown chart]
    PlotDrawdown -->|Comparison mode| PlotComparison[Plot comparison chart]
    PlotDrawdown -->|Single backtest| End([Reports Complete])
    PlotComparison --> End

    style CreateDirs fill:#FFB6C1
    style ExportEquity fill:#FFB6C1
    style ExportTrades fill:#FFB6C1
    style ExportMetrics fill:#FFB6C1
    style PlotEquity fill:#FFB6C1
    style PlotDrawdown fill:#FFB6C1
    style PlotComparison fill:#FFB6C1
```

## Execution Timeline Example

```mermaid
gantt
    title Stocktest Execution Timeline (3 tickers, 2 periods, 8 CPU cores)
    dateFormat SSS
    axisFormat %S.%L

    section Period 1
    Pre-fetch (parallel)          :a1, 000, 2000ms
    Backtest All (parallel)       :a2, after a1, 500ms
    Generate Reports              :a3, after a2, 1000ms

    section Period 2
    Pre-fetch (parallel)          :b1, after a3, 500ms
    Backtest All (parallel)       :b2, after b1, 500ms
    Generate Reports              :b3, after b2, 1000ms
```

## Key Characteristics

### Parallel Execution (GREEN in diagrams)
- **Data Fetching**: Up to 5 concurrent API requests via `asyncio.Semaphore`
  - Progress Tracking: `tqdm` progress bar updates in real-time
  - Concurrency Control: Semaphore prevents overwhelming the API
  - Location: `fetch_multiple_tickers_async()` in `fetcher.py`
- **Backtest Execution**: Up to CPU count concurrent backtests via `asyncio.Semaphore`
  - Each ticker's backtest runs independently in parallel
  - Concurrency Control: Semaphore limits to CPU count for optimal performance
  - Location: `_run_backtests_parallel()` in `cli.py`
- **Within Each Backtest**: Rebalance loop runs serially (state must be chronological)

### Serial Execution (PINK in diagrams)
- **Period Loop**: Each period runs sequentially
- **Report Generation**: Charts and CSVs generated one at a time after all backtests complete

### Cache Strategy (BLUE in diagrams)
- **Check Order**: no_data_ranges → prices table → yfinance API
- **Partial Hits**: Fetches only missing date ranges
- **No-Data Caching**: Prevents repeated failed API calls
- **Persistence**: SQLite database survives across sessions

### Error Handling
- **Per-Ticker Isolation**: Failed ticker doesn't stop others
  - Parallel data fetching: Continues fetching other tickers
  - Parallel backtests: Continues running other backtests
- **Retry Logic**: 3 retries with exponential backoff (up to 60s delay) for API calls
- **Graceful Degradation**: Returns None for failed tickers, continues with successful ones

### Performance Improvements
- **Before parallelization**:
  - 10 tickers @ 2s fetch + 2s backtest each = 40s total
- **After data fetch parallelization only**:
  - 10 tickers @ 2s fetch (parallel, max 5 concurrent) = 4s fetch + 20s backtest = 24s total
- **After full parallelization** (data + backtests):
  - 10 tickers @ 2s fetch (parallel, max 5) + 2s backtest (parallel, 8 cores) = 4s fetch + 3s backtest = **7s total**
  - **~83% faster than original serial execution**
