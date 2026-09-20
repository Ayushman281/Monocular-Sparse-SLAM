# Third-party components and provenance

## Pinned native sources

| Component | Exact revision | Role / upstream terms |
|---|---|---|
| [stella_vslam](https://github.com/stella-cv/stella_vslam) 0.7.0 | `525231147319bcd31242f981078c36d9272727b4` | SLAM core; original/fork BSD-2-Clause notices retained |
| [g2o](https://github.com/RainerKuemmerle/g2o) 20230223_git | `e8df2004e07ea8f5b8e6a8b9f2dc067b45b45036` | Optimization; component-specific BSD/LGPL/GPL notices, shared libraries |
| [FBoW](https://github.com/stella-cv/FBoW) | `c6e3c29e3332a0b0834021797e2aa4e8eb66a3c1` | Binary vocabulary/place recognition; MIT |
| [FBoW ORB vocabulary](https://github.com/stella-cv/FBoW_orb_vocab) | `708407ae4cd59219b996eda7ed1f4562c7ae106a` | Fixed pretrained ORB vocabulary; MIT notice in that repository |
| [tinycolormap](https://github.com/yuki-koyama/tinycolormap) | `67198d2b2b48ca5e97600c83b5c0f2310cfd4c03` | stella submodule; MIT |

Pins were obtained from upstream Git references and the 0.7.0 submodule tree on 2026-09-19. No pre-0.3 engine or ORB-SLAM3 code is used. `slam/dependencies.env` is the build lock. `slam/patches/offline-drain.patch` documents all engine modifications; use the identical patch on both providers. The hosted vocabulary download records SHA256 after fetching the immutable revision; no vocabulary was downloaded on the development PC.

The stella checkout includes nlohmann/json (MIT), spdlog/fmt (MIT) and source-derived libmv/OpenGV/OpenCV routines with their own MIT/BSD notices. Copies of license text and source-header attribution are retained in `third_party/licenses/`; upstream source fetches keep their original headers. stella's README specifically describes its `csparse_extension` dependency as LGPLv3+ and requests dynamic linking. The build uses shared g2o/FBoW/stella libraries; it does not assert the entire native image is MIT.

## System/runtime libraries

OpenCV (license varies with version, modern releases Apache-2.0), Eigen (MPL-2.0 plus component notices), yaml-cpp (MIT), SQLite (public domain), spdlog/fmt (MIT), SuiteSparse (component-specific licenses), FFmpeg (LGPL/GPL depending on the distribution's configured build), libstdc++ and OpenMP runtime are supplied by the Linux distribution. Debian 12 is the Docker baseline. Actual resolved package versions are written by the native build into `share/system-packages.txt` and must accompany the final benchmark/image audit. Distribution copyright files under `/usr/share/doc` are retained.

The selected g2o configuration disables CHOLMOD, GUI apps and examples, but stella's CMake also discovers SuiteSparse libraries. Inspect the built binary dependency graph and actual linked components before distributing a binary image; library link/license verification has not run. Retain relevant source availability/relinking materials required by the actual dependency licenses. Native source repositories are pinned and reproducibly fetched; final binary-distribution compliance is an acceptance item, not a blanket claim made from this table.

## Web application dependencies

| Component | Pin / license |
|---|---|
| Python | Docker 3.11 / PSF terms; actual patch/image digest pending build |
| FastAPI | 0.135.1 / MIT |
| Uvicorn | 0.41.0 / BSD-3-Clause |
| Pydantic | 2.12.5 / MIT |
| python-multipart | 0.0.22 / Apache-2.0 |
| NumPy | 2.2.6 / BSD-3-Clause plus bundled notices |
| PyYAML | 6.0.3 / MIT |
| React / React DOM | 19.3.0 / MIT |
| Three.js | 0.180.0 / MIT |
| Vite / React plugin | 8.3.0 / 6.1.1, MIT |
| TypeScript | 5.9.3 / Apache-2.0 |
| pytest / httpx | 8.4.2 / 0.28.1, MIT/BSD-3-Clause; hosted tests only |
| Nginx | 1.28 base tag / BSD-2-Clause; exact digest pending build |

The frontend lockfile records resolved versions/integrity and package-license metadata. Direct Python dependencies are pinned; transitive Python resolution and distribution patch versions must be recorded after the hosted environment is installed. Docker base tags are not immutable digests yet: record and pin tested digests for the final release. The original source license does not override dependency licenses.

## Alternatives not included

[ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) declares GPLv3. A future switch needs a documented technical reason and corresponding license/distribution review; it has not happened. [DROID-SLAM](https://github.com/princeton-vl/DROID-SLAM) was considered conceptually only. No neural network model, model service, training or fine-tuning is part of this project.
