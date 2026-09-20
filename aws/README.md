# AWS Deployment Guide

This runbook describes deployment of the complete frontend and backend to a single Ubuntu EC2 instance using Docker Compose. Nginx serves the compiled React frontend and proxies `/api` to the private FastAPI/native-SLAM container.

## Deployment status

The AWS configuration is included as a portable deployment option. It is not presented as an already completed AWS deployment. Region, instance type, costs, public URL, and performance must be recorded from the actual AWS environment.

## Architecture

```text
Internet
  -> EC2 security group: 80/443 public; 22 restricted
       -> Nginx + React container on host port 80
            -> /api over the private Compose network
                 -> FastAPI + native stella_vslam container on 8000
```

Backend port 8000 is intentionally not published to the host. All browser traffic uses a single Nginx origin.

## 1. Prerequisites and capacity planning

- AWS account with permission to create, inspect, stop, and terminate EC2 resources.
- Ubuntu 22.04 or 24.04 LTS x86_64 EC2 instance.
- Sufficient EBS storage for source, native compilation, Docker layers, and temporary uploads.
- SSH key or another approved EC2 connection method.
- Current Git repository or complete source package.

The supplied Compose configuration allows the backend up to 4 CPUs and 6 GiB RAM and defines a bounded 3 GiB `/tmp` tmpfs. Actual tmpfs usage consumes memory. Instance selection should therefore be based on measured build and benchmark results, not only free-tier eligibility.

Review current EC2, EBS, public IPv4, and data-transfer pricing before launch. Configure a budget alert and define a shutdown/termination plan. AWS notes that running instances can incur charges while idle; see the official [EC2 launch documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/LaunchingAndUsingInstances.html).

## 2. Launch the EC2 instance

Use the EC2 launch wizard to configure:

1. Ubuntu LTS x86_64 AMI.
2. Instance type supported by measured CPU and memory requirements.
3. EBS capacity for source, Docker images, compilation, and temporary data.
4. Public IPv4 address or Elastic IP when a stable endpoint is required.
5. Approved SSH key or access mechanism.

### Security-group ingress

| Port | Source | Purpose |
|---|---|---|
| 22/TCP | Administrator IP/CIDR only | SSH administration |
| 80/TCP | `0.0.0.0/0`; optionally `::/0` | HTTP application |
| 443/TCP | `0.0.0.0/0`; optionally `::/0` | HTTPS application |

Do not expose port 8000. AWS documents security groups as stateful instance firewalls and recommends restricting SSH to an administrative network; see [EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html) and [rule examples](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html).

## 3. Install Docker Engine and Compose

Connect through SSH and install Docker from its official Ubuntu repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl status docker --no-pager
sudo docker run --rm hello-world
```

These commands follow Docker's [Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/). Retain `sudo` unless a reviewed alternative Docker access model is configured.

## 4. Obtain the source

Clone the public repository:

```bash
cd /opt
sudo git clone \
  https://github.com/Ayushman281/Monocular-Sparse-SLAM.git \
  /opt/monocular-sparse-slam
sudo chown -R "$USER":"$USER" /opt/monocular-sparse-slam
cd /opt/monocular-sparse-slam
ls backend frontend slam scripts docker-compose.yml
```

Alternatively, extract the submitted source package to `/opt/monocular-sparse-slam`. Do not copy credentials, private videos, `.env` files, `node_modules`, local build output, or developer caches.

## 5. Configure the application

```bash
cd /opt/monocular-sparse-slam
cp .env.example .env
sed -i 's/^EXECUTION_TARGET=.*/EXECUTION_TARGET=aws/' .env
sed -i 's/^ENABLE_SLAM=.*/ENABLE_SLAM=true/' .env
```

Review `.env` before building. Defaults include a 200 MB upload limit, 30-second duration limit, 15 FPS processing target, 640-pixel longest-side bound, one active job, two OpenMP threads, and temporary result retention. Change these values only with capacity and benchmark evidence.

## 6. Build and start the services

The first image build compiles pinned native dependencies and may take several minutes.

```bash
cd /opt/monocular-sparse-slam
export APP_REVISION="$(git rev-parse HEAD 2>/dev/null || echo source-package)"
sudo --preserve-env=APP_REVISION docker compose build
sudo docker compose up -d
sudo docker compose ps
sudo docker compose logs --tail=100
```

Expected topology:

- frontend/Nginx published on host port 80;
- backend reachable only through Nginx `/api`; and
- no host mapping for backend port 8000.

## 7. Verify the deployment

Run on the EC2 host:

```bash
curl --fail http://127.0.0.1/api/health
curl --fail http://127.0.0.1/api/system
sudo docker compose ps
```

Required health fields:

```json
{"status":"healthy","slam_runner_available":true,"slam_enabled":true}
```

From an external computer, open:

```text
http://<EC2-PUBLIC-IP-OR-DNS>/
http://<EC2-PUBLIC-IP-OR-DNS>/api/health
```

Complete a real upload and verify visible landmarks, trajectory output, measured timing fields, and all three artifact downloads.

## 8. Performance benchmark

Run the benchmark from a controlled Python client on the EC2 host while Compose remains active:

```bash
cd /opt/monocular-sparse-slam
python3 -m venv .benchmark-venv
. .benchmark-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-test.txt
export EXECUTION_TARGET=aws
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --url http://127.0.0.1 \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

Use `--official` only with a clean committed checkout and a qualifying clip. Record the region, instance type, AMI/OS, CPU, RAM, Docker version, image IDs, container limits, input hash, individual runs, failures, and reconstruction statistics in [../benchmarks/benchmark_results.md](../benchmarks/benchmark_results.md).

## 9. HTTPS and domain configuration

Plain HTTP does not encrypt uploaded video. For an Internet-facing deployment, configure a domain and valid TLS certificate using a reviewed architecture such as:

- an Application Load Balancer with AWS Certificate Manager; or
- Certbot with a persistent Nginx/TLS configuration.

Open port 443 and redirect port 80 only after certificate validation. Do not report HTTPS as complete until it has been tested from an external network.

## 10. Operations

```bash
# Follow logs
sudo docker compose logs -f --tail=100

# Restart services
sudo docker compose restart

# Rebuild after a source update
sudo docker compose build
sudo docker compose up -d

# Stop and remove application containers/network
sudo docker compose down
```

In-memory jobs are lost on restart. Repeat health and real-video checks after any restart or rebuild. `docker compose down` does not stop EC2 billing; stop or terminate unused instances and review retained EBS volumes, snapshots, Elastic IPs, and other chargeable resources.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Native build is terminated | Use a host with more memory or reduce native build parallelism |
| Frontend reports backend unavailable | Check `/api/health`, both container logs, and backend health status |
| Upload returns HTTP 413 | Keep FastAPI upload limits and Nginx `client_max_body_size` consistent |
| Processing times out | Inspect preprocessing/native timing and resize the instance from measurement evidence |
| Port 80 is unreachable | Check container health, security-group ingress, subnet routing, Internet gateway, and public addressing |
| Build exhausts disk | Inspect Docker disk usage and EBS capacity before removing known unused artifacts |
