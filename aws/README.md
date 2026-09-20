# Deploy Assignment 2 on AWS

I designed this runbook to deploy both services to a single Ubuntu EC2 instance with Docker Compose. I use Nginx to serve the compiled React frontend and proxy `/api` to the private FastAPI/native-SLAM container.

## 1. Deployment architecture

```text
Internet
  └─ EC2 security group: 80/443 public, 22 restricted
       └─ Nginx + React container (host 80)
            └─ /api over the private Compose network
                 └─ FastAPI + native stella_vslam container (8000, not published)
```

I have prepared this as an AWS runbook; I am not claiming that I have already performed the AWS deployment. I will record the instance type, region, cost, public address, and performance from the actual account and host if I deploy there.

## 2. Prerequisites and sizing

For this deployment, I need:

- an AWS account with permission to create and terminate EC2 resources;
- an Ubuntu 22.04 or 24.04 LTS x86_64 EC2 instance;
- enough EBS space for source, native compilation, Docker layers, and uploaded videos;
- an SSH key or another approved EC2 access method; and
- the complete current source package or Git repository.

Choose the instance from benchmark evidence. The current Compose backend limit is 4 CPUs and 6 GiB RAM, plus a bounded 3 GiB `/tmp` tmpfs whose used contents consume memory. Do not choose a small instance merely because it is free-tier eligible; native compilation and SLAM may exceed it. Review current EC2 pricing, public IPv4 charges, storage, transfer, quota, and budget alerts before launch.

AWS notes that running instances can incur charges even while idle and recommends terminating them when finished. See the official [EC2 launch guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/LaunchingAndUsingInstances.html).

## 3. Create the EC2 instance

In the EC2 console:

1. Select an Ubuntu LTS x86_64 AMI.
2. Select an instance size supported by your measured CPU/RAM requirement.
3. Allocate sufficient EBS storage for the source and image build.
4. Enable a public IPv4 address or attach an Elastic IP if a stable address is required.
5. Create or select a security group with these inbound rules:

| Port | Source | Purpose |
|---|---|---|
| 22/TCP | Your administrator IP/CIDR only | SSH administration |
| 80/TCP | `0.0.0.0/0` (and `::/0` if using IPv6) | HTTP application |
| 443/TCP | `0.0.0.0/0` (and `::/0` if using IPv6) | HTTPS application |

Do **not** open backend port 8000 publicly. AWS documents security groups as the instance's stateful virtual firewall and recommends restricting SSH to the administrator's network; see [security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html) and [web-server rule examples](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html).

## 4. Install Docker Engine and Compose

Connect to the instance with SSH, then use Docker's official Ubuntu repository:

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

These commands follow Docker's current [Ubuntu installation documentation](https://docs.docker.com/engine/install/ubuntu/). Keep `sudo` on Docker commands unless the host owner deliberately configures another access model.

## 5. Transfer the source

Use Git, SCP, or SFTP to place the complete project on the instance. Never copy credentials, `.env` secrets, videos containing sensitive material, `node_modules`, local build output, or developer caches.

```bash
cd /opt
sudo mkdir -p monocular-sparse-slam
sudo chown "$USER":"$USER" monocular-sparse-slam
cd monocular-sparse-slam
# Clone the repository here, or extract/copy the submitted source package here.
ls backend frontend slam scripts docker-compose.yml
```

If cloning a repository, replace the placeholder with its real URL:

```bash
git clone <YOUR_GIT_REPOSITORY_URL> /opt/monocular-sparse-slam
cd /opt/monocular-sparse-slam
```

## 6. Configure the application

```bash
cd /opt/monocular-sparse-slam
cp .env.example .env
sed -i 's/^EXECUTION_TARGET=.*/EXECUTION_TARGET=aws/' .env
sed -i 's/^ENABLE_SLAM=.*/ENABLE_SLAM=true/' .env
```

Review `.env` before building. The defaults accept videos up to 200 MB/30 seconds, process at up to 15 FPS and 640 pixels on the longest side, allow one active job, use two OpenMP threads, and retain results temporarily. Adjust limits only with capacity and benchmark evidence.

## 7. Build and start both services

The first build compiles the pinned native dependencies and can take several minutes.

```bash
cd /opt/monocular-sparse-slam
export APP_REVISION="$(git rev-parse HEAD 2>/dev/null || echo source-package)"
sudo --preserve-env=APP_REVISION docker compose build
sudo docker compose up -d
sudo docker compose ps
sudo docker compose logs --tail=100
```

The frontend is published on host port 80. The backend is reachable only through Nginx at `/api`.

## 8. Verify the deployment

On the EC2 host:

```bash
curl --fail http://127.0.0.1/api/health
curl --fail http://127.0.0.1/api/system
sudo docker compose ps
```

The health response must contain:

```json
{"status":"healthy","slam_runner_available":true,"slam_enabled":true}
```

From another computer, open:

```text
http://<EC2-PUBLIC-IP-OR-DNS>/
http://<EC2-PUBLIC-IP-OR-DNS>/api/health
```

Then upload a real short RGB video and confirm that:

- the job completes without an error;
- landmarks and a trajectory appear;
- measured processing fields are populated; and
- all three downloads work.

## 9. Run the benchmark on AWS

Keep the Compose application running and execute the benchmark from a Python environment containing the backend test requirements, or from an equivalent controlled client:

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

Use `--official` only with a clean committed checkout and a qualifying clip. Record the EC2 instance type, region, AMI/OS, CPU, RAM, Docker version, image IDs, input hash, all run times, failures, and reconstruction statistics in [../benchmarks/benchmark_results.md](../benchmarks/benchmark_results.md).

## 10. HTTPS and a domain

For a submission demo, a public IP/DNS address can prove reachability, but HTTP does not encrypt video uploads. For an Internet-facing deployment, point a domain to the instance and configure TLS using a reviewed approach such as an Application Load Balancer with AWS Certificate Manager, or Certbot with an Nginx configuration that survives container updates. Open port 443 and redirect port 80 only after the certificate is valid.

Do not claim an HTTPS deployment until it has been tested from an external network.

## 11. Operations

```bash
# Follow logs
sudo docker compose logs -f --tail=100

# Restart both services
sudo docker compose restart

# Rebuild after a source update
sudo docker compose build
sudo docker compose up -d

# Stop and remove application containers/network
sudo docker compose down
```

After a restart, in-memory jobs are lost; health and a real upload must be checked again. `docker compose down` does not stop EC2 billing. Stop or terminate unused instances and check for retained EBS volumes, snapshots, Elastic IPs, and other chargeable resources.

## 12. Troubleshooting

- **Native build is killed:** select a host with more memory or reduce build parallelism in the Docker build configuration.
- **Frontend shows backend unavailable:** run `curl http://127.0.0.1/api/health`, inspect both container logs, and confirm the backend is healthy.
- **Upload returns 413:** keep FastAPI's size limit and Nginx `client_max_body_size` consistent.
- **Upload times out:** inspect backend timing/logs and size the EC2 instance from measured data rather than increasing timeouts blindly.
- **Port 80 is unreachable:** confirm the container is healthy, EC2 security-group ingress allows HTTP, the subnet route reaches an Internet gateway, and the instance has a public address.
- **Disk fills during builds:** inspect Docker disk use and EBS capacity; remove only known unused artifacts after verifying their targets.

## Deployment record

Complete this table on the actual AWS host:

| Field | Actual value |
|---|---|
| Date and source revision | Pending |
| AWS region / instance type / AMI | Pending |
| vCPUs / RAM / EBS | Pending |
| Docker and Compose versions | Pending |
| Image IDs/digests | Pending |
| Local health and real-video smoke test | Pending |
| Five-run benchmark result | Pending |
| Public URL and external-network test | Pending |
| HTTPS/domain status | Pending |
| Stop/termination and residual-cost check | Pending |
