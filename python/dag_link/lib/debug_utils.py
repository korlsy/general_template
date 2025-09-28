import os, json, time, signal, logging, socket, traceback
from datetime import datetime
from typing import Callable

def _read(path, default=""):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return default

def dump_sigterm_on_exit():
    def _handler(signum, frame):
        logging.error("[DEBUG] SIGTERM caught at %s. Stack:\n%s",
                      datetime.utcnow().isoformat(),
                      "".join(traceback.format_stack(frame)))
        # K8s가 종료猶予 내에 죽일 때 남는 마지막 줄
        time.sleep(0.5)
    signal.signal(signal.SIGTERM, _handler)
    signal.signal(signal.SIGINT, _handler)

def dump_cgroup_limits():
    # cgroup v2 기준 (대부분의 RHEL9)
    mem_max = _read("/sys/fs/cgroup/memory.max", "unknown")
    mem_current = _read("/sys/fs/cgroup/memory.current", "unknown")
    cpu_max = _read("/sys/fs/cgroup/cpu.max", "unknown")      # 예: "200000 100000" (quota period)
    cpu_weight = _read("/sys/fs/cgroup/cpu.weight", "unknown")
    logging.info("[DEBUG] cgroup: memory.max=%s memory.current=%s cpu.max=%s cpu.weight=%s",
                 mem_max, mem_current, cpu_max, cpu_weight)

def dump_proc_basics():
    uid, gid = os.getuid(), os.getgid()
    cwd = os.getcwd()
    hostname = socket.gethostname()
    env_pod = os.getenv("MY_POD_NAME") or hostname
    ns = os.getenv("MY_NAMESPACE") or os.getenv("AIRFLOW__KUBERNETES__NAMESPACE") or "default"
    image = os.getenv("MY_IMAGE") or "unknown"
    logging.info("[DEBUG] proc: uid=%s gid=%s cwd=%s", uid, gid, cwd)
    logging.info("[DEBUG] k8s: pod=%s ns=%s image=%s", env_pod, ns, image)
    # 마운트/디스크
    try:
        st = os.statvfs(".")
        logging.info("[DEBUG] disk: free=%dMB total=%dMB",
                     (st.f_bavail*st.f_frsize)//(1024*1024),
                     (st.f_blocks*st.f_frsize)//(1024*1024))
    except Exception as e:
        logging.info("[DEBUG] disk stat failed: %s", e)

def try_dump_k8s_events():
    """
    파드 이벤트를 로그에 복사 (클러스터 RBAC 허용 필요).
    kubernetes 파이썬 클라이언트가 이미지에 없으면 그냥 넘어갑니다.
    """
    try:
        from kubernetes import client, config
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pod = os.getenv("MY_POD_NAME") or socket.gethostname()
        ns = os.getenv("MY_NAMESPACE") or os.getenv("AIRFLOW__KUBERNETES__NAMESPACE") or "default"
        # 파드 describe 대용
        p = v1.read_namespaced_pod(name=pod, namespace=ns)
        logging.info("[DEBUG] pod.status.phase=%s node=%s startTime=%s",
                     p.status.phase, p.spec.node_name, p.status.start_time)
        # 이벤트
        evts = v1.list_namespaced_event(ns, field_selector=f"involvedObject.name={pod}")
        for e in evts.items[-10:]:  # 최근 10개만
            logging.info("[DEBUG] event: %s %s %s %s",
                         e.last_timestamp, e.type, e.reason, (e.message or "").strip()[:800])
    except Exception as e:
        logging.info("[DEBUG] k8s events skipped: %s", e)

def with_debug(func: Callable) -> Callable:
    """
    태스크 callable을 감싸서 실행 전/후 디버그 정보 로그로 남김
    """
    def wrapper(*args, **kwargs):
        dump_sigterm_on_exit()
        logging.info("[DEBUG] ===== PRE-MORTEM BEGIN =====")
        dump_proc_basics()
        dump_cgroup_limits()
        try_dump_k8s_events()
        logging.info("[DEBUG] ===== PRE-MORTEM END =====")
        try:
            result = func(*args, **kwargs)
            logging.info("[DEBUG] task result(type=%s) preview=%s",
                         type(result).__name__, str(result)[:300])
            return result
        except Exception as ex:
            logging.error("[DEBUG] Exception in task: %s", ex, exc_info=True)
            try_dump_k8s_events()
            raise
    return wrapper

def on_fail(context):
    ti = context.get("task_instance")
    logging.error("[DEBUG][on_fail] dag=%s task=%s try=%s run_id=%s log=%s",
                  getattr(context.get("dag"), "dag_id", None),
                  getattr(ti, "task_id", None),
                  getattr(ti, "try_number", None),
                  context.get("run_id"),
                  getattr(ti, "log_url", None))
    try_dump_k8s_events()

def on_success(context):
    ti = context["task_instance"]
    logging.info("[DEBUG][on_success] task=%s try=%s duration=%s",
                 ti.task_id, ti.try_number, (ti.end_date - ti.start_date) if ti.end_date and ti.start_date else None)
