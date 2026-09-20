# SLAM fundamentals and pipeline

## Camera geometry

A pinhole camera turns a camera-frame 3D point `(Xc,Yc,Zc)` into pixel coordinates `u=fx*Xc/Zc+cx`, `v=fy*Yc/Zc+cy`. The intrinsic matrix is `K=[[fx,0,cx],[0,fy,cy],[0,0,1]]`. `fx,fy` are focal lengths measured in pixels; `cx,cy` locate the principal point. Radial (`k1,k2,k3`) and tangential (`p1,p2`) coefficients describe lens distortion. They are not camera motion.

Extrinsics describe motion: `Tcw` maps world coordinates to camera coordinates. Its translation is not the position of the camera in the world. Inverting the rigid transform gives `Twc`, rotation `Rᵀ` and center `-Rᵀt`. The first successfully initialized camera establishes an arbitrary world reference. The application exports `Twc`; the viewer applies one rigid display rotation to the trajectory and map together.

## From frame to map

1. **Frame preparation.** Validate the input, rotate, resize and sample to CFR. Scale intrinsics alongside pixels. Sampling faster camera motion too sparsely can destroy track overlap.
2. **ORB extraction.** FAST detects corners across a pyramid; orientation and binary descriptors make matches more tolerant of rotation and modest scale changes. Descriptor Hamming distance counts differing bits. Repeated textures still cause ambiguity.
3. **Matching and geometry.** Descriptors propose correspondences. Epipolar constraints restrict where a match can lie. For calibrated normalized rays, the essential matrix relates two views; the fundamental matrix expresses the corresponding pixel-space relation. RANSAC repeatedly fits minimal hypotheses and scores inliers to reject mismatches.
4. **Initialization.** stella's perspective initializer evaluates homography/fundamental geometry and checks triangulated support, parallax and reprojection error. Translation supplies baseline. Pure rotation, distant flat scenes and too little texture may prevent initialization; returning a failure is correct behavior.
5. **Pose tracking.** Match current observations to previously mapped landmarks. PnP means pose from known 3D points and their 2D projections. Motion prediction, relocalization and pose-only refinement stabilize tracking; bad observations are discarded.
6. **Triangulation.** Two or more calibrated viewing rays and camera poses determine a 3D point by their intersection in the least-squares sense. Noise makes rays miss slightly. Enforce positive depth, parallax and reprojection consistency. Do not invent depth from a single 2D feature.
7. **Landmark management.** A landmark stores its 3D location, descriptor and keyframe observations. Newly observed map points are validated and duplicate or weak ones removed. This persistence distinguishes a map from disconnected per-frame features.
8. **Keyframes.** Retain informative views, not every frame. Too few keyframes lose useful baselines; too many increase optimization cost and redundancy. Covisibility connects keyframes that see common landmarks; a spanning tree maintains connectivity.
9. **Local bundle adjustment.** Refine nearby camera poses and landmark positions to minimize robust reprojection error: `Σ ρ(||u_observed - project(K,Tcw,Xw)||²)`. Gauge freedoms must be fixed. BA changes both cameras and points; pose-only optimization changes just the camera.
10. **Loop detection.** FBoW appearance similarity proposes places seen earlier. Temporal/covisibility rejection and geometric verification prevent nearby frames and lookalikes from becoming arbitrary constraints. A revisit alone is not evidence that the algorithm accepted a loop.
11. **Pose graph correction.** A verified loop connects previously separated parts of the trajectory. Monocular Sim(3) correction can reconcile rotation, translation and scale drift, followed by global bundle adjustment where invoked. Local refinements and loop correction reduce accumulated error; they do not guarantee a perfect map.
12. **Final export.** Finish queued optimization, stop threads, recompute frame poses from corrected reference keyframes, then export real finite landmarks and camera poses. Retain loss gaps and arbitrary-scale semantics.

## Why scale is unknown

Multiply every camera translation and landmark position by the same positive factor. Projection divides by depth, so the image coordinates do not change. Therefore a camera moving 10 cm through a small model can have the same image geometry as a camera moving 10 m through a proportionally larger scene. RGB pixels alone cannot distinguish them. A known distance, calibrated stereo baseline, reliable visual-inertial measurements or another external reference can supply metric scale; this app introduces none.

## Engine comparison and decision

| Approach | Fit and tradeoff | Decision |
|---|---|---|
| stella_vslam 0.7.0 | Native sparse feature tracking, map, optimization and loops; pinned dependency/build effort | Primary engine |
| ORB-SLAM3 | Feature-based visual/visual-inertial and multiple-map support; GPLv3 licensing | Alternative only if documented stella integration failure warrants a user-visible switch |
| DROID-SLAM | Learned recurrent SLAM with GPU/CUDA and checkpoint dependencies | No measured advantage for this CPU sparse-map assessment; not adopted |
| Custom OpenCV VO | Useful for explaining matching, essential/PnP and triangulation | Would require substantial additional map optimization, loop and relocalization work to become full SLAM |

C++ keeps the intensive frame/mapping work native. FastAPI is suitable for request validation and process orchestration. Sparse geometry matches the assessment and has a smaller browser payload than dense geometry. CPU deployment is an engineering starting point, not an assertion that any CPU meets the target. Python-only custom SLAM and offline COLMAP are not production substitutes here; SfM shares geometry but is not the specified sequential tracking/mapping service.

Sources: [pinned stella source](https://github.com/stella-cv/stella_vslam/tree/525231147319bcd31242f981078c36d9272727b4), [OpenCV calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html), [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3), [DROID-SLAM](https://github.com/princeton-vl/DROID-SLAM).
