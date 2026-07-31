-- =====================================================================
-- Dimensional model over OpenRouter's public data.
--
-- The one structural decision worth reading twice: the time key of every
-- fact is OUR capture date (`snapshot_date`), never the API's `date` field.
-- That field is the model's LAST DAY WITH TRAFFIC, not a series index.
-- Treating it as a time axis produces a convincing and entirely false chart.
-- =====================================================================


-- ---------------------------------------------------------------------
-- dim_model — SCD type 2 over price and context length.
-- Prices change, and capturing when they change is worth something on its own.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_model AS
WITH attrs AS (
    SELECT
        *,
        md5(concat_ws('|',
            coalesce(CAST(price_prompt     AS VARCHAR), '~'),
            coalesce(CAST(price_completion AS VARCHAR), '~'),
            coalesce(CAST(context_length   AS VARCHAR), '~')
        )) AS attr_hash
    FROM stg_models
    WHERE model_permaslug IS NOT NULL
),
marked AS (
    SELECT
        *,
        CASE
            WHEN attr_hash IS DISTINCT FROM lag(attr_hash) OVER w THEN 1
            ELSE 0
        END AS is_new_version
    FROM attrs
    WINDOW w AS (PARTITION BY model_permaslug ORDER BY snapshot_date)
),
versioned AS (
    SELECT
        *,
        sum(is_new_version) OVER (
            PARTITION BY model_permaslug
            ORDER BY snapshot_date
            ROWS UNBOUNDED PRECEDING
        ) AS version_num
    FROM marked
),
collapsed AS (
    SELECT
        model_permaslug,
        version_num,
        min(snapshot_date)                          AS valid_from,
        max(snapshot_date)                          AS last_seen,
        arg_max(model_id,          snapshot_date)   AS model_id,
        arg_max(name,              snapshot_date)   AS name,
        arg_max(author,            snapshot_date)   AS author,
        arg_max(context_length,    snapshot_date)   AS context_length,
        arg_max(created_ts,        snapshot_date)   AS created_ts,
        arg_max(price_prompt,      snapshot_date)   AS price_prompt,
        arg_max(price_completion,  snapshot_date)   AS price_completion,
        arg_max(price_cache_read,  snapshot_date)   AS price_cache_read,
        arg_max(input_modalities,  snapshot_date)   AS input_modalities,
        arg_max(output_modalities, snapshot_date)   AS output_modalities,
        arg_max(tokenizer,         snapshot_date)   AS tokenizer,
        arg_max(supports_tools,    snapshot_date)   AS supports_tools,
        arg_max(supports_reasoning, snapshot_date)  AS supports_reasoning
    FROM versioned
    GROUP BY model_permaslug, version_num
)
SELECT
    *,
    lead(valid_from) OVER (PARTITION BY model_permaslug ORDER BY version_num) AS valid_to,
    lead(valid_from) OVER (PARTITION BY model_permaslug ORDER BY version_num) IS NULL AS is_current
FROM collapsed;


-- ---------------------------------------------------------------------
-- fct_model_usage_snapshot — grain: (snapshot_date, window, model, variant)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE fct_model_usage_snapshot AS
SELECT
    snapshot_date,
    usage_window,
    model_permaslug,
    variant,
    CAST(prompt_tokens     AS HUGEINT) AS prompt_tokens,
    CAST(completion_tokens AS HUGEINT) AS completion_tokens,
    CAST(prompt_tokens AS HUGEINT) + CAST(completion_tokens AS HUGEINT) AS total_tokens,
    CAST(requests AS BIGINT)           AS requests,
    -- Descriptive attribute, explicitly NOT the time key. See header.
    source_last_activity_date,
    source_change
FROM stg_model_usage
WHERE model_permaslug IS NOT NULL;


-- ---------------------------------------------------------------------
-- dim_endpoint / fct_endpoint_perf_snapshot
--
-- WARNING carried in the data: these percentiles describe a 30-minute rolling
-- window (`window_minutes`), so one daily capture samples half an hour of the
-- day -- it does not summarise the day. Never average across snapshots without
-- weighting by stat_request_count.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_endpoint AS
SELECT
    endpoint_id,
    arg_max(model_permaslug,       snapshot_date) AS model_permaslug,
    arg_max(provider_name,         snapshot_date) AS provider_name,
    arg_max(provider_display_name, snapshot_date) AS provider_display_name,
    arg_max(provider_region,       snapshot_date) AS provider_region,
    arg_max(quantization,          snapshot_date) AS quantization,
    arg_max(context_length,        snapshot_date) AS context_length,
    arg_max(capacity_tpm,          snapshot_date) AS capacity_tpm,
    arg_max(supports_tools,        snapshot_date) AS supports_tools,
    arg_max(supports_reasoning,    snapshot_date) AS supports_reasoning,
    min(snapshot_date)                            AS first_seen,
    max(snapshot_date)                            AS last_seen
FROM stg_endpoint_perf
WHERE endpoint_id IS NOT NULL
GROUP BY endpoint_id;

CREATE OR REPLACE TABLE fct_endpoint_perf_snapshot AS
SELECT
    snapshot_date,
    endpoint_id,
    model_permaslug,
    variant,
    provider_name,
    status,
    is_deranked,
    is_disabled,
    price_prompt,
    price_completion,
    p50_throughput,
    p75_throughput,
    p90_throughput,
    p99_throughput,
    p50_latency,
    p90_latency,
    p99_latency,
    stat_request_count,
    window_minutes
FROM stg_endpoint_perf
WHERE endpoint_id IS NOT NULL;


-- ---------------------------------------------------------------------
-- fct_app_usage_snapshot
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE fct_app_usage_snapshot AS
SELECT
    snapshot_date,
    usage_window,
    app_id,
    rank,
    CAST(total_tokens   AS HUGEINT) AS total_tokens,
    CAST(total_requests AS BIGINT)  AS total_requests,
    app_title,
    app_origin_url
FROM stg_apps
WHERE app_id IS NOT NULL;


-- ---------------------------------------------------------------------
-- mart_model_fingerprint — the analytical core.
--
-- Two derived signals separate regimes of use that market share hides:
--   pc_ratio           context consumed per token produced
--   tokens_per_request size of one interaction
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE mart_model_fingerprint AS
WITH pivoted AS (
    SELECT
        snapshot_date,
        model_permaslug,
        variant,
        max(CASE WHEN usage_window = 'day'   THEN total_tokens END) AS day_tokens,
        max(CASE WHEN usage_window = 'week'  THEN total_tokens END) AS week_tokens,
        max(CASE WHEN usage_window = 'month' THEN total_tokens END) AS month_tokens,
        max(CASE WHEN usage_window = 'month' THEN prompt_tokens END)     AS month_prompt_tokens,
        max(CASE WHEN usage_window = 'month' THEN completion_tokens END) AS month_completion_tokens,
        max(CASE WHEN usage_window = 'month' THEN requests END)          AS month_requests,
        max(CASE WHEN usage_window = 'day'   THEN requests END)          AS day_requests,
        max(source_last_activity_date)                             AS source_last_activity_date
    FROM fct_model_usage_snapshot
    GROUP BY snapshot_date, model_permaslug, variant
),
with_model AS (
    SELECT
        p.*,
        m.name,
        m.author,
        m.created_ts,
        m.context_length,
        m.price_prompt,
        m.price_completion,
        m.supports_reasoning,
        -- How many days the model could possibly have accrued traffic in the
        -- 30-day window. Without this the month average divides by 30 for a
        -- model that has existed for four days.
        CASE
            WHEN m.created_ts IS NULL THEN 30
            ELSE least(30, greatest(
                date_diff('day', CAST(m.created_ts AS DATE), CAST(p.snapshot_date AS DATE)),
                0
            ))
        END AS effective_days,
        CASE
            WHEN m.created_ts IS NULL THEN NULL
            ELSE date_diff('day', CAST(m.created_ts AS DATE), CAST(p.snapshot_date AS DATE))
        END AS days_since_launch
    FROM pivoted p
    LEFT JOIN dim_model m
      ON m.model_permaslug = p.model_permaslug
     AND m.is_current
),
derived AS (
    SELECT
        *,
        CASE WHEN month_completion_tokens > 0
             THEN month_prompt_tokens::DOUBLE / month_completion_tokens END AS pc_ratio,
        CASE WHEN month_requests > 0
             THEN month_tokens::DOUBLE / month_requests END                 AS tokens_per_request,
        -- Age-corrected daily rate. effective_days is clamped to >= 1 so a
        -- model that launched today cannot divide by zero; such models are
        -- excluded from momentum by is_ratable anyway.
        CASE WHEN month_tokens > 0
             THEN month_tokens::DOUBLE / greatest(effective_days, 1) END    AS avg_daily_tokens
    FROM with_model
),
scored AS (
    SELECT
        *,
        CASE WHEN avg_daily_tokens > 0
             THEN day_tokens::DOUBLE / avg_daily_tokens END AS momentum_raw,
        -- Naive momentum, kept only to quantify how much the age correction
        -- matters. Never reported as a result.
        CASE WHEN month_tokens > 0
             THEN day_tokens::DOUBLE / (month_tokens::DOUBLE / 30) END AS momentum_uncorrected,
        (
            -- Age must be KNOWN, not assumed. 144 model-variants (mostly
            -- embedding models, absent from /api/v1/models) have no launch
            -- date; giving them the default 30-day denominator would report an
            -- uncorrected momentum as if it were corrected. They are 1.75% of
            -- tokens, so excluding them is cheap and keeps every published
            -- momentum genuinely age-corrected.
            created_ts IS NOT NULL
            AND coalesce(effective_days, 0) >= getvariable('min_days_momentum')
            AND coalesce(month_requests, 0) >= getvariable('min_month_requests')
        ) AS is_ratable
    FROM derived
)
SELECT
    snapshot_date,
    model_permaslug,
    variant,
    name,
    author,
    created_ts,
    days_since_launch,
    effective_days,
    context_length,
    price_prompt,
    price_completion,
    supports_reasoning,
    day_tokens,
    week_tokens,
    month_tokens,
    month_prompt_tokens,
    month_completion_tokens,
    month_requests,
    day_requests,
    pc_ratio,
    tokens_per_request,
    avg_daily_tokens,
    is_ratable,
    CASE WHEN is_ratable THEN momentum_raw END          AS momentum,
    CASE WHEN is_ratable THEN momentum_uncorrected END  AS momentum_uncorrected,
    -- Archetype. Cuts are declared constants, not fitted clusters: k-means on
    -- two axes with ~400 points yields clusters whose identity drifts between
    -- runs, and a cluster that changes meaning daily is useless in a series.
    CASE
        WHEN pc_ratio IS NULL OR tokens_per_request IS NULL THEN 'unclassified'
        WHEN pc_ratio < getvariable('pc_ratio_output_heavy') THEN 'output_heavy'
        WHEN pc_ratio >= getvariable('pc_ratio_high')
             AND tokens_per_request >= getvariable('tpr_high') THEN 'agentic'
        WHEN pc_ratio >= getvariable('pc_ratio_high')
             AND tokens_per_request <  getvariable('tpr_high') THEN 'extractive'
        ELSE 'conversational'
    END AS archetype,
    month_tokens::DOUBLE / nullif(sum(month_tokens) OVER (PARTITION BY snapshot_date), 0)
        AS token_share,
    row_number() OVER (PARTITION BY snapshot_date ORDER BY month_tokens DESC) AS token_rank,
    source_last_activity_date
FROM scored;


-- ---------------------------------------------------------------------
-- mart_archetype_stability — does the classification hold still?
--
-- This is the honest counterpart to picking fixed thresholds: rather than
-- assuming the cuts are stable, measure how many models change archetype
-- between consecutive captures. Empty until there are two snapshots.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE mart_archetype_stability AS
WITH seq AS (
    SELECT
        model_permaslug,
        variant,
        snapshot_date,
        archetype,
        lag(archetype)     OVER w AS prev_archetype,
        lag(snapshot_date) OVER w AS prev_snapshot_date
    FROM mart_model_fingerprint
    WHERE archetype <> 'unclassified'
    WINDOW w AS (PARTITION BY model_permaslug, variant ORDER BY snapshot_date)
)
SELECT
    snapshot_date,
    prev_snapshot_date,
    count(*)                                                   AS models_compared,
    sum(CASE WHEN archetype <> prev_archetype THEN 1 ELSE 0 END) AS reassignments,
    sum(CASE WHEN archetype <> prev_archetype THEN 1 ELSE 0 END)::DOUBLE
        / nullif(count(*), 0)                                  AS reassignment_rate
FROM seq
WHERE prev_archetype IS NOT NULL
GROUP BY snapshot_date, prev_snapshot_date;


-- ---------------------------------------------------------------------
-- mart_endpoint_price_perf — secondary analysis.
--
-- Cost against speed for every provider endpoint serving the same model. An
-- endpoint is Pareto-dominated when another endpoint for the same model is
-- both cheaper and faster; there is no rational reason to route to it.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE mart_endpoint_price_perf AS
WITH live AS (
    SELECT *
    FROM fct_endpoint_perf_snapshot
    WHERE p50_throughput IS NOT NULL
      AND price_completion IS NOT NULL
      AND coalesce(is_disabled, FALSE) = FALSE
      -- Percentiles over a 30-minute window with a handful of requests are
      -- noise, not measurement.
      AND coalesce(stat_request_count, 0) >= getvariable('min_endpoint_requests')
      AND snapshot_date = (SELECT max(snapshot_date) FROM fct_endpoint_perf_snapshot)
)
SELECT
    a.snapshot_date,
    a.model_permaslug,
    a.endpoint_id,
    a.provider_name,
    a.price_completion,
    a.p50_throughput,
    a.p50_latency,
    a.stat_request_count,
    count(b.endpoint_id) AS dominated_by_n,
    count(b.endpoint_id) > 0 AS is_dominated,
    -- Cheapest+fastest alternative, for the write-up.
    arg_min(b.provider_name, b.price_completion) AS dominant_provider
FROM live a
LEFT JOIN live b
       ON b.model_permaslug = a.model_permaslug
      AND b.endpoint_id <> a.endpoint_id
      AND b.price_completion <= a.price_completion
      AND b.p50_throughput   >= a.p50_throughput
      -- Strictly better on at least one axis, so identical endpoints do not
      -- dominate each other symmetrically.
      AND (b.price_completion < a.price_completion OR b.p50_throughput > a.p50_throughput)
GROUP BY ALL
-- Deterministic order: DuckDB gives no ordering guarantee, and without a
-- tiebreaker two endpoints tied on dominated_by_n swap places between runs,
-- which makes the generated report differ from itself and defeats the CI check
-- that it never goes stale.
ORDER BY a.model_permaslug, a.endpoint_id;
