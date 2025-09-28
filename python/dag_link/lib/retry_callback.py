import json
import os
import socket
import traceback as tb
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("airflow.task")
ISO = "%Y-%m-%dT%H:%M:%S.%f%z"

def _to_iso(dt):
    if hasattr(dt, "isoformat"):
        try:
            return dt.isoformat()
        except Exception:
            return str(dt)
    return str(dt)

def _safe(obj: Any):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        name = obj.__class__.__name__
        if name in {"DAG", "TaskInstance", "BaseOperator", "DagRun"}:
            d = {"_type": name}
            if name == "TaskInstance":
                d.update({
                    "dag_id": getattr(obj, "dag_id", None),
                    "task_id": getattr(obj, "task_id", None),
                    "run_id": getattr(obj, "run_id", None),
                    "try_number": getattr(obj, "try_number", None),
                    "max_tries": getattr(obj, "max_tries", None),
                    "map_index": getattr(obj, "map_index", None),
                    "state": str(getattr(obj, "state", None)),
                    "queue": getattr(obj, "queue", None),
                    "hostname": getattr(obj, "hostname", None),
                    "executor_config": getattr(obj, "executor_config", None),
                })
            if name == "BaseOperator":
                d.update({
                    "task_id": getattr(obj, "task_id", None),
                    "owner": getattr(obj, "owner", None),
                    "pool": getattr(obj, "pool", None),
                    "priority_weight": getattr(obj, "priority_weight", None),
                    "retries": getattr(obj, "retries", None),
                    "retry_delay": str(getattr(obj, "retry_delay", None)),
                    "queue": getattr(obj, "queue", None),
                })
            if name == "DAG":
                d.update({
                    "dag_id": getattr(obj, "dag_id", None),
                    "max_active_tasks": getattr(obj, "max_active_tasks", None),
                    "max_active_runs": getattr(obj, "max_active_runs", None),
                    "schedule_interval": str(getattr(obj, "schedule_interval", None)),
                })
            if name == "DagRun":
                d.update({
                    "dag_id": getattr(obj, "dag_id", None),
                    "run_id": getattr(obj, "run_id", None),
                    "run_type": str(getattr(obj, "run_type", None)),
                    "state": str(getattr(obj, "state", None)),
                    "external_trigger": getattr(obj, "external_trigger", None),
                    "conf": getattr(obj, "conf", None),
                    "logical_date": _to_iso(getattr(obj, "logical_date", None)),
                    "start_date": _to_iso(getattr(obj, "start_date", None)),
                })
            return d
        return str(obj)

def rich_on_retry_callback(context):
    try:
        ti = context.get("ti") or context.get("task_instance")
        task = context.get("task")
        dag = context.get("dag")
        dag_run = context.get("dag_run")

        exc = context.get("exception")
        tb_text = context.get("traceback") or (tb.format_exc() if exc else None)

        logical_date = context.get("logical_date") or context.get("ts") or context.get("execution_date")
        data_interval_start = context.get("data_interval_start")
        data_interval_end = context.get("data_interval_end")

        host = socket.gethostname()
        pod = os.environ.get("HOSTNAME")
        pid = os.getpid()

        log_url = None
        try:
            if ti and hasattr(ti, "log_url"):
                log_url = ti.log_url
        except Exception:
            pass

        logger.info("="*80)
        logger.info("[on_retry_callback] 재시도 디버그 덤프 시작")
        logger.info("-"*80)
        if ti:
            logger.info(" DAG       : %s", ti.dag_id)
            logger.info(" Task      : %s", ti.task_id)
            logger.info(" Run ID    : %s", getattr(ti, "run_id", None))
            logger.info(" Try#      : %s / MaxTries=%s", getattr(ti, "try_number", None), getattr(ti, "max_tries", None))
            logger.info(" MapIndex  : %s", getattr(ti, "map_index", None))
            logger.info(" State     : %s", getattr(ti, "state", None))
            logger.info(" Queue     : %s", getattr(ti, "queue", None))
            logger.info(" Hostname  : %s", getattr(ti, "hostname", None))
        else:
            logger.info(" TaskInstance: <None>")

        logger.info("-"*80)
        logger.info(" LogicalDate     : %s", _to_iso(logical_date))
        logger.info(" DataInterval    : start=%s  end=%s", _to_iso(data_interval_start), _to_iso(data_interval_end))
        logger.info(" Now(Worker)     : %s", _to_iso(datetime.now().astimezone()))
        logger.info("-"*80)
        if dag_run:
            logger.info(" DagRun.type     : %s", getattr(dag_run, "run_type", None))
            logger.info(" DagRun.state    : %s", getattr(dag_run, "state", None))
            logger.info(" DagRun.conf     : %s", getattr(dag_run, "conf", None))
        logger.info("-"*80)
        logger.info(" Host/PID        : host=%s  pod=%s  pid=%s", host, pod, pid)
        logger.info(" Log URL         : %s", log_url)
        if task:
            logger.info(" Retries/delay   : %s / %s", getattr(task, "retries", None), getattr(task, "retry_delay", None))
            logger.info(" Pool/Queue      : %s / %s", getattr(task, "pool", None), getattr(task, "queue", None))
        if dag:
            logger.info(" DAG concurrency : max_active_tasks=%s  max_active_runs=%s  schedule_interval=%s",
                        getattr(dag, "max_active_tasks", None),
                        getattr(dag, "max_active_runs", None),
                        getattr(dag, "schedule_interval", None))
        logger.info("-"*80)
        if exc:
            logger.info("[Exception] type=%s  msg=%s", exc.__class__.__name__, exc)
        if tb_text:
            logger.info("[Traceback]\n%s", tb_text.strip())
        logger.info("-"*80)

        payload = {
            "kind": "on_retry_callback_dump",
            "when": datetime.now().astimezone().isoformat(),
            "host": {"hostname": host, "pod": pod, "pid": pid},
            "ti": _safe(ti),
            "task": _safe(task),
            "dag": _safe(dag),
            "dag_run": _safe(dag_run),
            "schedule": {
                "logical_date": _to_iso(logical_date),
                "data_interval_start": _to_iso(data_interval_start),
                "data_interval_end": _to_iso(data_interval_end),
            },
            "urls": {"log_url": log_url},
            "exception": {
                "type": exc.__class__.__name__ if exc else None,
                "message": str(exc) if exc else None,
                "traceback": tb_text,
            },
        }
        logger.info("[JSON]\n%s", json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        logger.info("="*80)

    except Exception as e:
        logger.error("[on_retry_callback] 콜백 처리 중 에러 발생: %s", e)
