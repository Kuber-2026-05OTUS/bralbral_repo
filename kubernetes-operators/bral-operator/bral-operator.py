import kopf
import kubernetes.client
import structlog
from kubernetes.client.rest import ApiException

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,  # добавляем уровень (INFO, ERROR...)
        structlog.processors.KeyValueRenderer(
            key_order=["timestamp", "level", "event", "name", "namespace"]
        ),
    ]
)
logger = structlog.get_logger()

kubernetes.config.load_incluster_config()
api = kubernetes.client.AppsV1Api()
core_api = kubernetes.client.CoreV1Api()


def create_pv(name: str, storage_size: str):
    """Создаёт PersistentVolume (кластерный)"""
    pv_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": f"{name}-pv", "labels": {"app": "mysql", "cr": name}},
        "spec": {
            "capacity": {"storage": storage_size},
            "accessModes": ["ReadWriteOnce"],
            "hostPath": {"path": f"/mnt/data/{name}"},
            "persistentVolumeReclaimPolicy": "Retain",
        },
    }
    try:
        core_api.create_persistent_volume(body=pv_manifest)
        logger.info("PV created", name=name)
    except ApiException as e:
        if e.status != 409:
            logger.error("Failed to create PV", name=name, error=str(e))
            raise


def create_pvc(name: str, storage_size: str, namespace: str):
    """Создаёт PersistentVolumeClaim в указанном namespace"""
    pvc_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": f"{name}-pvc",
            "namespace": namespace,
            "labels": {"app": "mysql", "cr": name},
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": storage_size}},
        },
    }
    try:
        core_api.create_namespaced_persistent_volume_claim(
            namespace=namespace, body=pvc_manifest
        )
        logger.info("PVC created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "Failed to create PVC", name=name, namespace=namespace, error=str(e)
            )
            raise


def create_service(name: str, namespace: str):
    """Создаёт Service типа ClusterIP"""
    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": "mysql", "cr": name},
        },
        "spec": {
            "selector": {"app": "mysql", "cr": name},
            "ports": [{"port": 3306, "targetPort": 3306}],
            "type": "ClusterIP",
        },
    }
    try:
        core_api.create_namespaced_service(namespace=namespace, body=service_manifest)
        logger.info("Service created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "Failed to create Service", name=name, namespace=namespace, error=str(e)
            )
            raise


def create_deployment(
    name: str, namespace: str, image: str, database: str, password: str
):
    """Создаёт Deployment для MySQL (без storage_size, т.к. он не нужен в Deployment)"""
    deployment_manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": "mysql", "cr": name},
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": "mysql", "cr": name}},
            "template": {
                "metadata": {"labels": {"app": "mysql", "cr": name}},
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
        api.create_namespaced_deployment(namespace=namespace, body=deployment_manifest)
        logger.info("Deployment created", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 409:
            logger.error(
                "Failed to create Deployment",
                name=name,
                namespace=namespace,
                error=str(e),
            )
            raise


@kopf.on.create("otus.homework", "v1", "mysqls")
def mysql_on_create(body, **kwargs):
    name = body["metadata"]["name"]
    namespace = body["metadata"]["namespace"]
    spec = body["spec"]
    image = spec["image"]
    database = spec["database"]
    password = spec["password"]
    storage_size = spec["storage_size"]

    logger.info("Processing MySQL resource", name=name, namespace=namespace)

    # PV (кластерный) – namespace не нужен
    create_pv(name, storage_size)

    # PVC
    create_pvc(name, storage_size, namespace)

    # Service
    create_service(name, namespace)

    # Deployment
    create_deployment(name, namespace, image, database, password)

    logger.info("All resources created successfully", name=name, namespace=namespace)


@kopf.on.delete("otus.homework", "v1", "mysqls")
def mysql_on_delete(body, **kwargs):
    name = body["metadata"]["name"]
    namespace = body["metadata"]["namespace"]

    logger.info("Deleting resources for MySQL", name=name, namespace=namespace)

    # Удаляем Deployment
    try:
        api.delete_namespaced_deployment(name=name, namespace=namespace)
        logger.info("Deployment deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "Failed to delete Deployment",
                name=name,
                namespace=namespace,
                error=str(e),
            )
            raise

    # Удаляем Service
    try:
        core_api.delete_namespaced_service(name=name, namespace=namespace)
        logger.info("Service deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "Failed to delete Service", name=name, namespace=namespace, error=str(e)
            )
            raise

    # Удаляем PVC
    try:
        core_api.delete_namespaced_persistent_volume_claim(
            name=f"{name}-pvc", namespace=namespace
        )
        logger.info("PVC deleted", name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(
                "Failed to delete PVC", name=name, namespace=namespace, error=str(e)
            )
            raise

    # Удаляем PV (кластерный)
    try:
        core_api.delete_persistent_volume(name=f"{name}-pv")
        logger.info("PV deleted", name=name)
    except ApiException as e:
        if e.status != 404:
            logger.error("Failed to delete PV", name=name, error=str(e))
            raise

    logger.info("All resources deleted successfully", name=name, namespace=namespace)
