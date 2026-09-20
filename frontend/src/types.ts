export type Reconstruction = {
  job_id: string;
  video: { duration_seconds: number; input_width: number; input_height: number; input_fps: number; processing_width: number; processing_height: number; processed_fps: number };
  processing: { processing_time_seconds: number; slam_process_seconds: number; preprocessing_seconds: number; postprocessing_seconds: number; real_time_factor: number; target_met: boolean };
  slam: { frames_processed: number; frames_tracked: number; keyframes: number; map_points: number; loop_edges: number };
  trajectory: number[][];
  keyframe_trajectory: number[][];
  points: number[][];
  warnings: string[];
};
export type Camera = {mode: 'approximate'|'calibrated'; horizontal_fov: number; fx: number; fy: number; cx: number; cy: number; cols: number; rows: number; k1:number; k2:number; p1:number; p2:number; k3:number};
