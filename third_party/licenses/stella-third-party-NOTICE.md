
The following files are derived from third-party libraries.

- `./3rd/json` : [nlohmann/json \[v3.6.1\]](https://github.com/nlohmann/json) (MIT license)
- `./3rd/spdlog` : [gabime/spdlog \[v1.3.1\]](https://github.com/gabime/spdlog) (MIT license)
- `./3rd/tinycolormap` : [yuki-koyama/tinycolormap](https://github.com/yuki-koyama/tinycolormap) (MIT license)
- `./3rd/FBoW` : [stella-cv/FBoW](https://github.com/stella-cv/FBoW) (MIT license) (forked from [rmsalinas/fbow](https://github.com/rmsalinas/fbow))
- `./src/stella_vslam/solver/essential_5pt.h` : part of [libmv/libmv](https://github.com/libmv/libmv) (MIT license)
- `./src/stella_vslam/solver/pnp_solver.cc` : part of [laurentkneip/opengv](https://github.com/laurentkneip/opengv) (3-clause BSD license)
- `./src/stella_vslam/feature/orb_extractor.cc` : part of [opencv/opencv](https://github.com/opencv/opencv) (3-clause BSD License)
- `./src/stella_vslam/feature/orb_point_pairs.h` : part of [opencv/opencv](https://github.com/opencv/opencv) (3-clause BSD License)

Please use `g2o` as the dynamic link library because `csparse_extension` module of `g2o` is LGPLv3+.

