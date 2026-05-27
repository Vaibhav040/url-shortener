import time
import logging
import requests
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect

# ── Configuration ─────────────────────────────────────────
PROMETHEUS_URL = "http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
WEBHOOK_URL = "https://webhook.site/c40e34b3-3ef9-4950-b9a0-64b1ddea5e4b"
NAMESPACE = "url-shortener"
CHECK_INTERVAL = 30        # seconds between checks
CPU_THRESHOLD = 80         # percent — scale up above this
MEMORY_THRESHOLD = 85      # percent — alert above this
CRASH_THRESHOLD = 3        # restart count before remediation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


# ── Webhook Alert ─────────────────────────────────────────
def send_alert(title: str, message: str, severity: str = "warning"):
    payload = {
        "title": title,
        "message": message,
        "severity": severity,
        "namespace": NAMESPACE,
        "source": "url-shortener-remediation-operator"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        logger.info(f"Alert sent: {title} — status {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")


# ── Remediation Actions ───────────────────────────────────
def restart_pod(v1: client.CoreV1Api, pod_name: str, reason: str):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=NAMESPACE)
        logger.info(f"Restarted pod {pod_name} — reason: {reason}")
        send_alert(
            title=f"Pod Restarted: {pod_name}",
            message=f"Auto-remediation restarted pod due to: {reason}",
            severity="warning"
        )
    except Exception as e:
        logger.error(f"Failed to restart pod {pod_name}: {e}")


def scale_deployment(apps_v1: client.AppsV1Api, deployment_name: str, current_replicas: int):
    new_replicas = current_replicas + 1
    try:
        apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=NAMESPACE,
            body={"spec": {"replicas": new_replicas}}
        )
        logger.info(f"Scaled {deployment_name} from {current_replicas} to {new_replicas} replicas")
        send_alert(
            title=f"Deployment Scaled: {deployment_name}",
            message=f"High CPU detected — scaled from {current_replicas} to {new_replicas} replicas",
            severity="warning"
        )
    except Exception as e:
        logger.error(f"Failed to scale deployment {deployment_name}: {e}")


# ── Check 1: CrashLoopBackOff ─────────────────────────────
def check_crashloop(v1: client.CoreV1Api):
    pods = v1.list_namespaced_pod(namespace=NAMESPACE)
    for pod in pods.items:
        for container_status in (pod.status.container_statuses or []):
            if container_status.restart_count >= CRASH_THRESHOLD:
                state = container_status.state
                if state.waiting and state.waiting.reason == "CrashLoopBackOff":
                    logger.warning(f"CrashLoopBackOff detected: {pod.metadata.name}")
                    restart_pod(v1, pod.metadata.name, "CrashLoopBackOff")


# ── Check 2: High CPU via Prometheus ─────────────────────
def check_high_cpu(prom: PrometheusConnect, apps_v1: client.AppsV1Api):
    query = f'''
        sum(rate(container_cpu_usage_seconds_total{{
            namespace="{NAMESPACE}",
            container!=""
        }}[5m])) by (pod) /
        sum(kube_pod_container_resource_limits{{
            namespace="{NAMESPACE}",
            resource="cpu"
        }}) by (pod) * 100
    '''
    try:
        result = prom.custom_query(query=query)
        for item in result:
            cpu_percent = float(item["value"][1])
            pod_name = item["metric"].get("pod", "")
            if cpu_percent > CPU_THRESHOLD:
                logger.warning(f"High CPU {cpu_percent:.1f}% on pod {pod_name}")
                deployments = apps_v1.list_namespaced_deployment(namespace=NAMESPACE)
                for deployment in deployments.items:
                    if deployment.metadata.name == "url-shortener":
                        current = deployment.spec.replicas
                        if current < 5:
                            scale_deployment(apps_v1, deployment.metadata.name, current)
    except Exception as e:
        logger.error(f"CPU check failed: {e}")


# ── Check 3: OOMKilled ────────────────────────────────────
def check_oom(v1: client.CoreV1Api):
    pods = v1.list_namespaced_pod(namespace=NAMESPACE)
    for pod in pods.items:
        for container_status in (pod.status.container_statuses or []):
            last_state = container_status.last_state
            if last_state and last_state.terminated:
                if last_state.terminated.reason == "OOMKilled":
                    logger.warning(f"OOMKilled detected: {pod.metadata.name}")
                    restart_pod(v1, pod.metadata.name, "OOMKilled — memory limit exceeded")
                    send_alert(
                        title=f"OOMKilled: {pod.metadata.name}",
                        message="Pod exceeded memory limit and was killed. Consider increasing memory limits.",
                        severity="critical"
                    )


# ── Main Loop ─────────────────────────────────────────────
def main():
    logger.info("Starting URL Shortener Remediation Operator")
    logger.info(f"Watching namespace: {NAMESPACE}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")

    # Load K8s config — in-cluster when running in pod
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config")
    except Exception:
        config.load_kube_config()
        logger.info("Loaded local kubeconfig")

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

    while True:
        logger.info("Running remediation checks...")
        try:
            check_crashloop(v1)
            check_high_cpu(prom, apps_v1)
            check_oom(v1)
        except Exception as e:
            logger.error(f"Remediation cycle failed: {e}")

        logger.info(f"Checks complete. Sleeping {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()