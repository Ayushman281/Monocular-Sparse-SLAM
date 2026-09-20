FROM python:3.11-slim-bookworm AS native
ENV DEBIAN_FRONTEND=noninteractive EXECUTION_TARGET=aws SLAM_PREFIX=/opt/slam BUILD_JOBS=2
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake ninja-build git \
    curl ca-certificates pkg-config libeigen3-dev libopencv-dev libyaml-cpp-dev libsqlite3-dev \
    libsuitesparse-dev libspdlog-dev libgl1-mesa-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY slam/ slam/
COPY third_party/ third_party/
COPY scripts/hosted_guard.sh scripts/build_native.sh scripts/download_vocab.sh scripts/
RUN bash scripts/build_native.sh && bash scripts/download_vocab.sh

FROM python:3.11-slim-bookworm AS runtime
ARG APP_REVISION=unrecorded
ENV APP_REVISION=${APP_REVISION}
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    EXECUTION_TARGET=disabled ENABLE_SLAM=false API_HOST=0.0.0.0 API_PORT=8000 \
    SLAM_RUNNER=/opt/slam/bin/slam_runner SLAM_VOCAB=/opt/slam/share/orb_vocab.fbow \
    JOB_ROOT=/tmp/slam-jobs LD_LIBRARY_PATH=/opt/slam/lib OMP_NUM_THREADS=2
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    libopencv-calib3d406 libopencv-features2d406 libopencv-videoio406 libopencv-highgui406 \
    libyaml-cpp0.7 libsqlite3-0 libspdlog1.10 libgomp1 libcxsparse3 libspqr2 \
    libamd2 libcamd2 libcolamd2 libccolamd2 libsuitesparseconfig5 libmetis5 liblapack3 libblas3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 slam
WORKDIR /app
COPY --from=native /opt/slam /opt/slam
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY scripts/cloud_backend.py scripts/cloud_backend.py
COPY third_party third_party
USER slam
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health')); assert d['status']=='healthy'"
CMD ["python", "scripts/cloud_backend.py"]
