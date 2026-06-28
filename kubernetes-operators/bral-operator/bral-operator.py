import kopf
import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from structlog.dev import ConsoleRenderer

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        ConsoleRenderer(),
    ]
)
logger = structlog.get_logger()

try:
    # будет внутри кубера брать
    config.load_incluster_config()
except config.ConfigException:
    # возьмем из локального .kube/confg
    config.load_kube_config()

core_api = client.CoreV1Api()
apps_api = client.AppsV1Api()


def create_pv(name: str, storage_size: str):
    manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": f"{name}-pv"},
        "spec": {
            "capacity": {"storage": storage_size},
            "accessModes": ["ReadWriteOnce"],
            "hostPath": {"path": f"/mnt/data/{name}"},
            "persistentVolumeReclaimPolicy": "Retain",
        },
    }
    try:
        core_api.create_persistent_volume(manifest)
        logger.info("pv_created", name=name)
    except ApiException as e:
        if e.status != 409:
            logger.error("pv_create_failed", name=name, error=str(e))
            raise


def create_pvc(name: str, storage_size: str, namespace: str):
    manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": f"{name}-pvc", "namespace": namespace},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": storage_size}},
        },
    }
    try:
        core_api.create_namespaced_persistent_volume_claim(
            namespace=namespace, body=manifest
        )
        logger.info("pvc_created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "pvc_create_failed", name=name, namespace=namespace, error=str(e)
            )
            raise


def create_service(name: str, namespace: str):
    manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "selector": {"app": name},
            "ports": [{"port": 3306, "targetPort": 3306}],
        },
    }
    try:
        core_api.create_namespaced_service(namespace=namespace, body=manifest)
        logger.info("service_created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "service_create_failed", name=name, namespace=namespace, error=str(e)
            )
            raise


def create_deployment(
    name: str, namespace: str, image: str, database: str, password: str
):
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [
                        {
                            "name": "mysql",
                            "image": image,
                            "env": [
                                {"name": "MYSQL_ROOT_PASSWORD", "value": password},
                                {"name": "MYSQL_DATABASE", "value": database},
                            ],
                            "ports": [{"containerPort": 3306}],
                            "volumeMounts": [
                                {"name": "storage", "mountPath": "/var/lib/mysql"}
                            ],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "storage",
                            "persistentVolumeClaim": {"claimName": f"{name}-pvc"},
                        }
                    ],
                },
            },
        },
    }
    try:
        apps_api.create_namespaced_deployment(namespace=namespace, body=manifest)
        logger.info("deployment_created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "deployment_create_failed", name=name, namespace=namespace, error=str(e)
            )
            raise


@kopf.on.create("otus.homework", "v1", "mysqls")
def create_mysql(spec, name, namespace, **kwargs):
    logger.info("processing_create", name=name, namespace=namespace)
    create_pv(name=name, storage_size=spec["storage_size"])
    create_pvc(name=name, storage_size=spec["storage_size"], namespace=namespace)
    create_service(name=name, namespace=namespace)
    create_deployment(
        name=name,
        namespace=namespace,
        image=spec["image"],
        database=spec["database"],
        password=spec["password"],
    )
    logger.info("all_resources_created", name=name, namespace=namespace)


@kopf.on.delete("otus.homework", "v1", "mysqls")
def delete_mysql(name, namespace, **kwargs):
    logger.info("processing_delete", name=name, namespace=namespace)
    try:
        apps_api.delete_namespaced_deployment(name=name, namespace=namespace)
        logger.info("deployment_deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "deployment_delete_failed", name=name, namespace=namespace, error=str(e)
            )
            raise
    try:
        core_api.delete_namespaced_service(name=name, namespace=namespace)
        logger.info("service_deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "service_delete_failed", name=name, namespace=namespace, error=str(e)
            )
            raise
    try:
        core_api.delete_namespaced_persistent_volume_claim(
            name=f"{name}-pvc", namespace=namespace
        )
        logger.info("pvc_deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "pvc_delete_failed", name=name, namespace=namespace, error=str(e)
            )
            raise
    try:
        core_api.delete_persistent_volume(name=f"{name}-pv")
        logger.info("pv_deleted", name=name)
    except ApiException as e:
        if e.status != 404:
            logger.error("pv_delete_failed", name=name, error=str(e))
            raise
    logger.info("all_resources_deleted", name=name, namespace=namespace)
