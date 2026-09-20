# Assignment 2 execution policy

This directory is the independent Monocular RGB Sparse Point Cloud SLAM assignment. The parent directory contains Assignment 1's Qwen business-card application; do not modify it for SLAM work. This assignment explicitly uses pinned stella_vslam, not Qwen or another neural-model substitute.

On the development PC, edit/inspect source and run frontend-only Vite preview on loopback. Frontend dependency installation with scripts disabled is allowed. Do not run backend services, native compilation, unit tests, typechecks, production builds, Docker, calibration, sample generators, vocabulary downloads or SLAM here, including WSL.

Backend/native testing belongs on an explicitly selected hosted Lightning AI Studio or the user's AWS server. Keep `EXECUTION_TARGET` explicit and `ENABLE_SLAM=false` by default. The same source/engine/patch must support both providers through configuration. No training or fine-tuning is needed.

Full Docker/public deployment acceptance belongs on AWS. Verify costs, credit balance, account plan, regional availability and quota before creating resources, with the user's billing approval. Do not create new resources before hosted native validation. Never request/expose secrets.

Record unexecuted checks in docs/validation.md. Never claim runtime acceptance, a public URL, loop detections, accuracy or <=10-second performance from source inspection or UI preview. Use actual real-video benchmarks and preserve failures. Do not fabricate production outputs or history.
