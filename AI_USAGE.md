# AI Usage

## Tools used

I used ChatGPT throughout this assignment with the **Astra 6** and **GPT-5.6 Sol**
large language models. I did not use another AI development tool for this
submission. Both models were used across multiple development iterations. I did
not maintain a model-by-model attribution log, so the recommendations below are
attributed to ChatGPT rather than to one individual model.

## Extent of AI assistance

I estimate that approximately **80% of my assignment code was generated or
substantially assisted by AI**. This is my personal estimate rather than a
measured line-by-line attribution. It includes application source,
native-integration code, tests, configuration, deployment scripts, and
documentation. I am stating this directly so that my use of AI is transparent.

AI assistance covered:

- interpreting the assignment and translating it into technical requirements;
- proposing the React → FastAPI → C++ → stella_vslam architecture;
- inspecting the pinned stella_vslam interfaces and preparing the native runner integration;
- implementing video validation, preprocessing, camera configuration, job lifecycle, output parsing, and API behavior;
- implementing the React/Three.js upload, status, metrics, download, and visualization interface;
- preparing unit-test, HTTP smoke-test, calibration, and repeated-benchmark tooling;
- preparing Lightning AI and AWS/Docker deployment files;
- troubleshooting errors from real Lightning logs; and
- drafting and organizing the technical and submission documentation.

## My contribution and responsibility

I did not write every line independently, but I reviewed and modified the project and developed a good understanding of its purpose, architecture, data flow, deployment process, and limitations. In particular, I:

- clarified the required deployment workflow and service boundaries;
- ran the installation and services in Lightning AI;
- supplied and interpreted real native-build, Conda, npm, and hosting output;
- changed backend hosting code and setup scripts;
- required frontend and backend installation to be performed from their respective folders;
- configured and checked the separate 8000/5173 service arrangement;
- made decisions about the submitted deployment instructions; and
- accept responsibility for validating and explaining the final submission.

## Significant recommendations adopted

ChatGPT, through Astra 6 and GPT-5.6 Sol, proposed the following recommendations.
I reviewed them, understood their tradeoffs, and adopted them in the project:

- Separate performance-critical SLAM execution from HTTP orchestration.
- Pin stella_vslam, g2o, FBoW, and the ORB vocabulary to exact revisions.
- Use calibrated camera intrinsics when available, with a clearly labelled field-of-view approximation as a fallback.
- Keep AWS and Lightning on the same application/native engine and vary only deployment configuration.
- Proxy relative `/api` requests through the public frontend service instead of embedding provider-specific backend URLs.
- Preserve relative/arbitrary scale and export only actual engine geometry.
- Report measured timing fields and retain raw benchmark failures instead of presenting synthetic success values.

## Recommendations rejected or modified

I rejected or modified the following ChatGPT-generated recommendations after
reviewing them against the real Lightning environment and project requirements:

- **Nested Python virtual environment:** rejected after Lightning AI reported that Studios allow only the existing Conda environment. The scripts now use the active Python 3.11+ interpreter directly on Lightning.
- **Incomplete native dependency list:** modified after the real CMake error showed that g2o's exported package required OpenGL/GLX development files. `libgl1-mesa-dev` was added while the graphical viewer remains disabled.
- **Single root-level installation workflow:** I changed this workflow so that backend installation/start occurs from `backend/` and frontend installation/start occurs independently from `frontend/`.
- **Hard-coded public backend URL/CORS:** rejected in favor of a same-origin proxy from frontend port 5173 to private backend port 8000.
- **Illustrative but unsupported engine parameters:** not copied blindly; configuration is limited to parameters supported by the pinned stella_vslam revision.
- **Synthetic geometry, loop events, and performance values:** rejected. The application and documentation require actual runtime results.

## Verification boundary

I understand that AI-generated source and recommendations are not evidence that a native build, reconstruction, deployment, or performance target passed. I treat real command output, a real uploaded video, a public health check, and repeated measurements as the authoritative evidence. I am responsible for completing those checks and correcting any issue found before submission.
