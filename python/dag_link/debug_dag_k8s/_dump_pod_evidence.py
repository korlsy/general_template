import traceback, pathlib
from kubernetes import client, config

def _incluster_namespace() -> str:
    p = pathlib.Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
    return p.read_text().strip() if p.exists() else "default"

def dump_pod_evidence(context):
    ti = context["ti"]
    ns = _incluster_namespace()
    try:
        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()
        v1 = client.CoreV1Api()
        ls = (
            f"airflow.apache.org/dag_id={ti.dag_id},"
            f"airflow.apache.org/task_id={ti.task_id},"
            f"airflow.apache.org/try_number={ti.try_number}"
        )
        pods = v1.list_namespaced_pod(namespace=ns, label_selector=ls).items
        if not pods:
            print(f"[EVIDENCE] no pod. ns={ns} labels=[{ls}]")
            return
        for p in pods:
            print(f"[EVIDENCE] pod={p.metadata.name} phase={p.status.phase} node={p.spec.node_name}")
            cs_list = p.status.container_statuses or []
            for cs in cs_list:
                term = cs.state.terminated if cs.state and cs.state.terminated else None
                if term:
                    print(f"[EVIDENCE] container={cs.name} exit={term.exit_code} "
                          f"reason={term.reason} signal={term.signal}\n{term.message or ''}")
            evs = v1.list_namespaced_event(
                ns, field_selector=f"involvedObject.name={p.metadata.name}"
            ).items
            for e in evs[-20:]:
                print(f"[EVENT] {e.last_timestamp} {e.type} {e.reason} {e.message}")
    except Exception as e:
        print("[EVIDENCE] error:", e)
        print(traceback.format_exc())
