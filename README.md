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

- `minikube delete && minikube start`
- `cd kubernetes-security`
- `kubectl apply -f namespace.yaml`
- `kubectl apply -f security.yaml`
- `kubectl apply -f config-map.yaml`
- `kubectl apply -f deployment.yaml`
- `kubectl port-forward -n homework deployment/angie-deployment 8080:8000`
- `curl http://localhost:8080/metrics.html`