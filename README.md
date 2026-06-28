# Репозиторий для выполнения домашних заданий курса "Инфраструктурная платформа на основе Kubernetes-2026-05" 


## Useful commands

### 1. kubernetes-into

```bash
kubectl create -f ./kubernetes-intro/namespace.yaml
```

```bash
kubectl config set-context --current --namespace=homework
```

```bash
kubectl config view --minify | grep namespace
```

```bash
kubectl apply -f ./kubernetes-intro/pod.yaml
```


```bash
kubectl get pods
```

```bash
kubectl describe pod angie
```

```bash
kubectl logs angie
```

```bash
kubectl exec -it angie -- sh
```

```bash
kubectl delete pod angie -n homework
kubectl apply -f ./kubernetes-intro/pod.yaml
```

```bash
kubectl exec -n homework angie -- angie -T
```

### 2. kubernetes-controlers

```bash
kubectl get nodes --show-labels
```

```bash
kubectl label node minikube homework=true
```

```bash
kubectl apply -f ./kubernetes-controllers
```

```bash
kubectl rollout status deployment angie-deployment
```

```bash
kubectl get pods -l app=angie -w
```

```bash
kubectl get deployment angie-deployment -o yaml | grep -A5 strategy
```


```bash
kubectl describe deployment angie-deployment
```

### 3. kubernetes-networks

- `minikube delete && minikube start`
- `cd kubernetes-networks`
- `kubectl apply -f namespace.yaml`
- `kubectl config set-context --current --namespace=homework`
- `kubectl apply -f ./additional/manifests/configMap.yaml`
- `kubectl apply -f deployment.yaml`
- `kubectl get gatewayclass`

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get gatewayclass
error: the server doesn't have a resource type "gatewayclass"
```

- `kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml`

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get gatewayclass
No resources found

```


-   ```bash
    helm repo add traefik https://traefik.github.io/charts && helm repo update && \
    helm install traefik traefik/traefik --namespace traefik --create-namespace -f ./additional/helm/traefic-values.yaml
    ```


```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ helm repo add traefik https://traefik.github.io/charts && helm repo update && \
helm install traefik traefik/traefik --namespace traefik --create-namespace -f ./additional/helm/traefic-values.yaml
"traefik" already exists with the same configuration, skipping
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "longhorn" chart repository
...Successfully got an update from the "traefik" chart repository
...Successfully got an update from the "grafana" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
NAME: traefik
LAST DEPLOYED: Sat Jun 13 12:55:38 2026
NAMESPACE: traefik
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
traefik with docker.io/traefik:v3.7.4 has been deployed successfully on traefik namespace!

⚠️ DEPRECATION WARNING: Gateway API CRDs will no longer be shipped with this chart in a future major version.
You will need to install them yourself before deploying Traefik v3.7:
  kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml

```

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get gatewayclass
NAME      CONTROLLER                      ACCEPTED   AGE
traefik   traefik.io/gateway-controller   True       81s
```


- `kubectl apply -f gateway.yaml`

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl apply -f gateway.yaml 
gateway.gateway.networking.k8s.io/homework-gateway created
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get gateway
NAME               CLASS     ADDRESS   PROGRAMMED   AGE
homework-gateway   traefik                          12s
```

- `kubectl apply -f service.yaml`

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl apply -f service.yaml 
service/angie-service created
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get svc
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
angie-service   ClusterIP   10.108.71.217   <none>        8000/TCP   2s
```


- `kubectl apply -f httpRoute.yaml`

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl apply -f httpRoute.yaml 
httproute.gateway.networking.k8s.io/homework-route created
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-networks$ kubectl get httproute
NAME             HOSTNAMES           AGE
homework-route   ["homework.otus"]   5s
```

```bash
helm upgrade --install traefik traefik/traefik \
  -n traefik \
  -f ./additional/helm/traefic-values.yaml
```

`kubectl get gateway -n homework`

```bash
ubuntu@ubuntu-MS-7C52:~$ kubectl get gateway -n homework
NAME               CLASS     ADDRESS        PROGRAMMED   AGE
homework-gateway   traefik   10.99.131.10   True         34m
```


```bash
echo "10.99.131.10 homework.otus" | sudo tee -a /etc/hosts
```


- `kubectl port-forward -n traefik service/traefik 8000:8000`

- `curl http://homework.otus/index.html`


### 4. kubernetes-volumes

- `minikube delete && minikube start`
- `cd kubernetes-volumes`
- `kubectl config set-context --current --namespace=homework`
- `kubectl apply -f namespace.yaml && kubectl apply -f cm.yaml && kubectl apply -f pvc.yaml && kubectl apply -f deployment.yaml`

`kubectl get pods`

```bash
NAME                                READY   STATUS    RESTARTS   AGE
angie-deployment-6f9d677887-fvppv   1/1     Running   0          11m
angie-deployment-6f9d677887-qv5r6   1/1     Running   0          11m
angie-deployment-6f9d677887-tg742   1/1     Running   0          11m
```

```
kubectl exec -it angie-deployment-6f9d677887-fvppv -- sh -c "wget -qO- http://127.0.0.1:8000/conf/angie-default.conf"
```


```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl exec -it angie-deployment-6f9d677887-fvppv -- sh -c "wget -qO- http://127.0.0.1:8000/conf/angie-default.conf"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
server {
    listen 8000;

    root /homework;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
    
}
```

```bash
kubectl exec -it angie-deployment-74789cf9f-7mlhk -- sh -c "echo 'The new episode 8 of From airs on June 14, 2026.' > /homework/test-pvc"
```

```bash
kubectl delete pod angie-deployment-74789cf9f-7mlhk
pod "angie-deployment-74789cf9f-7mlhk" deleted from homework namespace
```

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl get pods
NAME                               READY   STATUS    RESTARTS   AGE
angie-deployment-74789cf9f-jr999   1/1     Running   0          14m
angie-deployment-74789cf9f-kmldh   1/1     Running   0          16s
angie-deployment-74789cf9f-mhrks   1/1     Running   0          14m
```

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl exec -it angie-deployment-74789cf9f-kmldh -- sh -c "cat /homework/test-pvc"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
The new episode 8 of From airs on June 14, 2026.
```

```bash
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl delete deployment angie-deployment
deployment.apps "angie-deployment" deleted from homework namespace
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl get deployments
No resources found in homework namespace.
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl get pvc
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS        VOLUMEATTRIBUTESCLASS   AGE
homework-pvc   Bound    pvc-b5b9fadd-9cfe-416f-bb9a-2d0381f685b6   1Gi        RWO            homework-hostpath   <unset>                 3m53s
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl apply -f deployment.yaml 
deployment.apps/angie-deployment created
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$ kubectl get pods
NAME                               READY   STATUS    RESTARTS   AGE
angie-deployment-74789cf9f-42nk2   1/1     Running   0          16s
angie-deployment-74789cf9f-62xzr   1/1     Running   0          16s
angie-deployment-74789cf9f-gsknl   1/1     Running   0          16s
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-volumes$  kubectl exec -it angie-deployment-74789cf9f-62xzr -- sh -c "cat /homework/test-pvc"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
The new episode 8 of From airs on June 14, 2026.
```
### 5. kubernetes-security

#### Контейнерная часть
- `minikube delete && minikube start`
- `cd kubernetes-security`
- `kubectl apply -f namespace.yaml`
- `kubectl apply -f security.yaml`
- `kubectl apply -f config-map.yaml`
- `kubectl apply -f deployment.yaml`

#### Часть с генерацией kubeconfig ( выполнять после первой части)

- `cd temp`
- `kubectl create token cd -n homework --duration 24h > token`
- `export API_SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')`
- `echo $API_SERVER`
- `kubectl get configmap kube-root-ca.crt -n kube-public -o jsonpath='{.data.ca\.crt}' > cluster-ca.crt`
- `cat cluster-ca.crt`

- Генерация kubeconfig:

```
kubectl config set-cluster homework-cluster \
  --server=$API_SERVER \
  --certificate-authority=cluster-ca.crt \
  --embed-certs=true \
  --kubeconfig=cd.kubeconfig

kubectl config set-credentials cd \
  --token=$(cat token) \
  --kubeconfig=cd.kubeconfig

kubectl config set-context cd-context \
  --cluster=homework-cluster \
  --user=cd \
  --namespace=homework \
  --kubeconfig=cd.kubeconfig

kubectl config use-context cd-context --kubeconfig=cd.kubeconfig
```
- `kubectl --kubeconfig=cd.kubeconfig get pods -n homework`


### 6. kubernetes-templating


#### Задание 1: Создание чарта на основе прошлых ДЗ

- `minikube delete && minikube start`
- `cd kubernetes-templating`

- Установка helm

```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
chmod 700 get_helm.sh
./get_helm.sh

```

- `helm create homework-app`


- Удалить мусор

```
cd homework-app
rm templates/*.yaml
rm templates/tests/*
```

- `helm dependency update` ( for redis repo)
- `helm lint .`
- `helm template homework .`
- `helm install homework . -n homework --create-namespace`
- `helm status homework -n homework`
- `helm list -n homework`
- `helm upgrade homework . --set replicaCount=5`
- `helm history homework`

- ```
helm upgrade homework . \
  --set image.repository=docker.angie.software/angie \
  --set image.tag=1.12.0
```

- `helm rollback homework 2`

- `helm get manifest homework`

- `helm install homework . --dry-run`

- `helm get values homework`

- `helm get values homework --all`

- `kubectl get pods -n homework`

```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get pods -n homework
NAME                                    READY   STATUS    RESTARTS   AGE
homework-homework-app-cf6677d5f-4hf8j   1/1     Running   0          11m
homework-homework-app-cf6677d5f-d49b8   1/1     Running   0          11m
homework-homework-app-cf6677d5f-d6klv   1/1     Running   0          11m
homework-redis-master-0                 1/1     Running   0          11m
```

- `helm uninstall homework -n homework`


#### Задание 2: kafka через helmfile

- `minikube delete && minikube start`
- `cd kubernetes-templating`

- Установка helmfile (https://helmfile.readthedocs.io/en/latest/#installation)
- ```
# Скачиваем архив для Linux amd64
wget https://github.com/helmfile/helmfile/releases/download/v1.6.0/helmfile_1.6.0_linux_amd64.tar.gz

# Распаковываем архив
tar -xzvf helmfile_1.6.0_linux_amd64.tar.gz

# Перемещаем распакованный бинарник в /usr/local/bin/
sudo mv helmfile /usr/local/bin/

# Проверяем версию
helmfile version
```

```
helm repo add bitnami https://charts.bitnami.com/bitnami

helm repo update
```

```
helmfile template
```



```
helmfile apply
```

```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ helmfile apply
Adding repo bitnami https://charts.bitnami.com/bitnami
"bitnami" has been added to your repositories
Comparing release=kafka-prod, chart=bitnami/kafka, namespace=prod
Comparing release=kafka-dev, chart=bitnami/kafka, namespace=dev
in ./helmfile.yaml: command "/usr/local/bin/helm" exited with non-zero status:

PATH:
  /usr/local/bin/helm

ARGS:
  0: helm (4 bytes)
  1: diff (4 bytes)
  2: upgrade (7 bytes)
  3: --allow-unreleased (18 bytes)
  4: kafka-prod (10 bytes)
  5: bitnami/kafka (13 bytes)
  6: --kube-version (14 bytes)
  7: 1.35.1 (6 bytes)
  8: --namespace (11 bytes)
  9: prod (4 bytes)
  10: --values (8 bytes)
  11: /tmp/helmfile2588986964/prod-kafka-prod-values-76b77c678c (57 bytes)
  12: --reset-values (14 bytes)
  13: --detailed-exitcode (19 bytes)

ERROR:
  exit status 1

EXIT STATUS
  1

STDERR:
  Error: unknown command "diff" for "helm"
  Run 'helm --help' for usage.

COMBINED OUTPUT:
  Error: unknown command "diff" for "helm"
  Run 'helm --help' for usage.
```

```
helm plugin list
```

```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ helm plugin list
NAME    VERSION TYPE    APIVERSION      PROVENANCE      SOURCE

```




```
helmfile sync
```

```

```
helm plugin install https://github.com/databus23/helm-diff --version v3.15.10
```

```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ helm plugin install https://github.com/databus23/helm-diff --version v3.15.10 --verify=false
WARNING: Skipping plugin signature verification
Downloading https://github.com/databus23/helm-diff/releases/download/v3.15.10/helm-diff-linux-amd64.tgz
Preparing to install into /home/ubuntu/.local/share/helm/plugins/helm-diff
Installed plugin: diff
```


```
helmfile apply
```

```
Upgrading release=kafka-dev, chart=bitnami/kafka, namespace=dev
Upgrading release=kafka-prod, chart=bitnami/kafka, namespace=prod
Release "kafka-dev" does not exist. Installing it now.
NAME: kafka-dev
LAST DEPLOYED: Sat Jun 27 20:55:38 2026
NAMESPACE: dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
CHART NAME: kafka
CHART VERSION: 32.4.3
APP VERSION: 4.0.0

⚠ WARNING: Since August 28th, 2025, only a limited subset of images/charts are available for free.
    Subscribe to Bitnami Secure Images to receive continued support and security updates.
    More info at https://bitnami.com and https://github.com/bitnami/containers/issues/83267

** Please be patient while the chart is being deployed **

Kafka can be accessed by consumers via port 9092 on the following DNS name from within your cluster:

    kafka-dev.dev.svc.cluster.local

Each Kafka broker can be accessed by producers via port 9092 on the following DNS name(s) from within your cluster:

    kafka-dev-controller-0.kafka-dev-controller-headless.dev.svc.cluster.local:9092
    kafka-dev-controller-1.kafka-dev-controller-headless.dev.svc.cluster.local:9092
    kafka-dev-controller-2.kafka-dev-controller-headless.dev.svc.cluster.local:9092

To create a pod that you can use as a Kafka client run the following commands:

    kubectl run kafka-dev-client --restart='Never' --image docker.io/bitnami/kafka:4.0.0-debian-12-r10 --namespace dev --command -- sleep infinity
    kubectl exec --tty -i kafka-dev-client --namespace dev -- bash

    PRODUCER:
        kafka-console-producer.sh \
            --bootstrap-server kafka-dev.dev.svc.cluster.local:9092 \
            --topic test

    CONSUMER:
        kafka-console-consumer.sh \
            --bootstrap-server kafka-dev.dev.svc.cluster.local:9092 \
            --topic test \
            --from-beginning

WARNING: There are "resources" sections in the chart not set. Using "resourcesPreset" is not recommended for production. For production installations, please set the following values according to your workload needs:
  - controller.resources
  - defaultInitContainers.prepareConfig.resources
+info https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
Listing releases matching ^kafka-dev$
kafka-dev       dev             1               2026-06-27 20:55:38.499425255 +0100 BST deployed        kafka-32.4.3    4.0.0      
Release "kafka-prod" does not exist. Installing it now.
NAME: kafka-prod
LAST DEPLOYED: Sat Jun 27 20:55:38 2026
NAMESPACE: prod
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
CHART NAME: kafka
CHART VERSION: 32.4.3
APP VERSION: 4.0.0

⚠ WARNING: Since August 28th, 2025, only a limited subset of images/charts are available for free.
    Subscribe to Bitnami Secure Images to receive continued support and security updates.
    More info at https://bitnami.com and https://github.com/bitnami/containers/issues/83267

** Please be patient while the chart is being deployed **

Kafka can be accessed by consumers via port 9092 on the following DNS name from within your cluster:

    kafka-prod.prod.svc.cluster.local

Each Kafka broker can be accessed by producers via port 9092 on the following DNS name(s) from within your cluster:

    kafka-prod-controller-0.kafka-prod-controller-headless.prod.svc.cluster.local:9092

The CLIENT listener for Kafka client connections from within your cluster have been configured with the following security settings:
    - SASL authentication

To connect a client to your Kafka, you need to create the 'client.properties' configuration files with the content below:

security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
    username="admin" \
    password="$(kubectl get secret kafka-prod-user-passwords --namespace prod -o jsonpath='{.data.client-passwords}' | base64 -d | cut -d , -f 1)";

To create a pod that you can use as a Kafka client run the following commands:

    kubectl run kafka-prod-client --restart='Never' --image docker.io/bitnami/kafka:3.5.2 --namespace prod --command -- sleep infinity
    kubectl cp --namespace prod /path/to/client.properties kafka-prod-client:/tmp/client.properties
    kubectl exec --tty -i kafka-prod-client --namespace prod -- bash

    PRODUCER:
        kafka-console-producer.sh \
            --producer.config /tmp/client.properties \
            --bootstrap-server kafka-prod.prod.svc.cluster.local:9092 \
            --topic test

    CONSUMER:
        kafka-console-consumer.sh \
            --consumer.config /tmp/client.properties \
            --bootstrap-server kafka-prod.prod.svc.cluster.local:9092 \
            --topic test \
            --from-beginning

WARNING: There are "resources" sections in the chart not set. Using "resourcesPreset" is not recommended for production. For production installations, please set the following values according to your workload needs:
  - controller.resources
  - defaultInitContainers.prepareConfig.resources
+info https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

⚠ SECURITY WARNING: Original containers have been substituted. This Helm chart was designed, tested, and validated on multiple platforms using a specific set of Bitnami and Tanzu Application Catalog containers. Substituting other containers is likely to cause degraded security and performance, broken chart features, and missing environment variables.

Substituted images detected:
  - docker.io/bitnami/kafka:3.5.2

⚠ WARNING: Original containers have been retagged. Please note this Helm chart was tested, and validated on multiple platforms using a specific set of Bitnami and Bitnami Secure Images containers. Substituting original image tags could cause unexpected behavior.

Retagged images:
  - docker.io/bitnami/kafka:3.5.2
WARNING: Rolling tag detected (bitnami/kafka:3.5.2), please note that it is strongly recommended to avoid using rolling tags in a production environment.
+info https://techdocs.broadcom.com/us/en/vmware-tanzu/application-catalog/tanzu-application-catalog/services/tac-doc/apps-tutorials-understand-rolling-tags-containers-index.html
Listing releases matching ^kafka-prod$
kafka-prod      prod            1               2026-06-27 20:55:38.542111212 +0100 BST deployed        kafka-32.4.3    4.0.0      

========== Updated Releases ==========
NAME         NAMESPACE   CHART           VERSION   DURATION
kafka-dev    dev         bitnami/kafka   32.4.3          2s
kafka-prod   prod        bitnami/kafka   32.4.3          2s
```

```
helm search repo bitnami/kafka --versions
```



```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ helm list -n prod
helm list -n dev
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
kafka-prod      prod            1               2026-06-27 20:55:38.542111212 +0100 BST deployed        kafka-32.4.3    4.0.0      
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
kafka-dev       dev             1               2026-06-27 20:55:38.499425255 +0100 BST deployed        kafka-32.4.3    4.0.0      
```


```
helm status kafka-prod -n prod
helm status kafka-dev -n dev
```


```
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ kubectl get svc -n prod
kubectl get svc -n dev
NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
kafka-prod                       ClusterIP   10.101.57.161   <none>        9092/TCP                     2m19s
kafka-prod-controller-headless   ClusterIP   None            <none>        9094/TCP,9092/TCP,9093/TCP   2m19s
NAME                            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
kafka-dev                       ClusterIP   10.97.84.40   <none>        9092/TCP                     2m19s
kafka-dev-controller-headless   ClusterIP   None          <none>        9094/TCP,9092/TCP,9093/TCP   2m19s
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo/kubernetes-templating/kafka$ 

```


helmfile destroy
```


### 7. kubernetes-operators

- `minikube delete && minikube start`
- `cd kubernetes-security`