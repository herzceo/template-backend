# Monitoring & Production Stack Rules

The production stack lives in `docker-compose.prod.yaml` + `monitoring/`. It is
separate from `docker-compose.local.yaml` (which stays dev-only). Run it with
`just prod-up | prod-down | prod-logs [svc] | prod-delete`.

## Topology

- **nginx** (`monitoring/nginx/nginx.conf`) is the ONLY service that publishes a
  host port (`:80`). `/` → `backend:8000`, `/grafana/` → `grafana:3000`. HTTP only;
  TLS is left to the deployer (documented inline in the conf).
- All services share one compose network (`template.prod.stack`). Nothing except
  nginx is reachable from the host. `backend`/`queue` keep outbound internet for
  OAuth/Resend/S3 — do not move them onto an `internal: true` network.
- Image tags are pinned (`postgres:18`/`redis:8` follow the local-compose major-tag
  convention; everything else pins an exact version).

## Metrics

- **HTTP**: Litestar's `litestar.plugins.prometheus` plugin. `create_api`
  (`backend/entry/rest/main/api.py`) builds `PrometheusConfig(app_name=NAME,
  group_path=True)`, adds `prometheus_config.middleware`, and registers
  `PrometheusController` (serves `/metrics` at root). `/metrics` is excluded from
  `SessionMiddleware`. Path is Litestar's default `/metrics` — not configurable.
- **Queue worker**: no ASGI surface, so `entry/queue/main.py` calls
  `prometheus_client.start_http_server(WORKER_METRICS_PORT)` (default `9091`).
  Metric objects are module-level singletons in
  `backend/infra/database/psql/dbus/metrics.py` and are incremented inside
  `QueueExecutor` (`executor.py`). Metric names are a contract with
  `monitoring/grafana/dashboards/queue.json` — keep them in sync:
  `queue_jobs_total{queue,status}`, `queue_job_duration_seconds` (histogram),
  `queue_jobs_in_progress`, `queue_worker_up`.

When adding a new long-running process that needs metrics, follow the queue
pattern: a `metrics.py` module of `prometheus_client` singletons in its layer, a
`start_http_server` call in its `entry/` bootstrap, and a Prometheus scrape job.

## Prometheus scrape targets (`monitoring/prometheus/prometheus.yml`)

`backend:8000`, `queue:9091`, `postgres-exporter:9187`, `redis-exporter:9121`,
`node-exporter:9100`, `localhost:9090`. Adding a target = add an exporter service
to `docker-compose.prod.yaml` + a scrape job here + (optionally) a dashboard.

## Logs

Grafana **Alloy** (`monitoring/alloy/config.alloy`) discovers all containers via
the Docker socket and ships stdout/stderr to **Loki**. App logging stays plain
stdlib `logging` — no code change needed for logs to reach Loki.

## Grafana

Provisioned, not hand-configured. Datasources (`Prometheus` default + `Loki`) and
the dashboard file-provider are under `monitoring/grafana/provisioning/`.
Dashboards (`queue`, `postgres`, `redis`, `server`, `prometheus`) are JSON in
`monitoring/grafana/dashboards/` and all reference the `prometheus` datasource uid.
Admin credentials come from `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD`
in `.env` — never hardcode them in compose (the compose uses a `:?` required-var
guard).
