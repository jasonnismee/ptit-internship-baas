def get_namespace_yaml(name: str):
    return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {name}
"""

def get_service_yaml(namespace: str):
    return f"""apiVersion: v1
kind: Service
metadata:
  name: geth-headless
  namespace: {namespace}
spec:
  clusterIP: None
  ports:
    - port: 30303
      name: p2p
  selector:
    app: geth
"""

def get_genesis_yaml(namespace: str, chain_id: int, address: str):
    # Tạo extradata cho Clique consensus
    clean_address = address.replace("0x", "")
    extradata = "0x" + "0" * 64 + clean_address + "0" * 130
    
    genesis_json = f"""{{
  "config": {{
    "chainId": {chain_id},
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "clique": {{
      "period": 5,
      "epoch": 30000
    }}
  }},
  "difficulty": "1",
  "gasLimit": "8000000",
  "extradata": "{extradata}",
  "alloc": {{
    "{address}": {{ 
      "balance": "1000000000000000000000" 
    }}
  }}
}}"""
    
    return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: geth-genesis
  namespace: {namespace}
data:
  genesis.json: |
{chr(10).join('    ' + line for line in genesis_json.split(chr(10)))}
"""

def get_statefulset_yaml(namespace: str, replicas: int, chain_id: int, address: str):
    return f"""apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: node
  namespace: {namespace}
  labels:
    app: geth
spec:
  serviceName: "geth-headless"
  podManagementPolicy: Parallel
  replicas: {replicas}
  selector:
    matchLabels:
      app: geth
  template:
    metadata:
      labels:
        app: geth
    spec:
      containers:
      - name: geth
        image: ethereum/client-go:v1.13.5
        imagePullPolicy: IfNotPresent
        command: ["/bin/sh", "-c"]
        args:
          - |
            POD_IP=$(hostname -i)
            echo "Starting Geth at IP: $POD_IP"
            geth --datadir /data \\
            --networkid {chain_id} \\
            --http --http.addr "0.0.0.0" --http.api "eth,net,web3,personal,admin,miner" \\
            --http.corsdomain "*" --http.vhosts "*" \\
            --metrics --metrics.addr "0.0.0.0" --metrics.port 6060 \\
            --mine --miner.etherbase {address} \\
            --unlock {address} \\
            --password /etc/geth-pass/password \\
            --allow-insecure-unlock \\
            --nodiscover \\
            --cache=64 \\
            --nat extip:$POD_IP
        ports:
        - containerPort: 8545
        - containerPort: 30303
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: password-secret
          mountPath: /etc/geth-pass
          readOnly: true
      initContainers:
      - name: init-genesis
        image: ethereum/client-go:v1.13.5
        command: ["/bin/sh", "-c"]
        args:
          - |
            sleep 10
            if [ ! -d /data/geth ]; then
              echo "Initializing Genesis..."
              geth init --datadir /data /config/genesis.json
            fi
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: genesis-config
          mountPath: /config
      - name: import-account
        image: ethereum/client-go:v1.13.5
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo "Importing Private Key..."
            rm -rf /data/keystore
            geth account import --datadir /data --password /etc/geth-pass/password --lightkdf /etc/secret/key
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: account-secret
          mountPath: /etc/secret
          readOnly: true
        - name: password-secret
          mountPath: /etc/geth-pass
          readOnly: true
      volumes:
      - name: genesis-config
        configMap:
          name: geth-genesis
      - name: account-secret
        secret:
          secretName: geth-account-key
      - name: password-secret
        secret:
          secretName: geth-pass
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
"""
