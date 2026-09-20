#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include <stella_vslam/config.h>
#include <stella_vslam/system.h>
#include <stella_vslam/publish/map_publisher.h>
#include <stella_vslam/data/keyframe.h>
#include <stella_vslam/data/graph_node.h>
#include <stella_vslam/data/landmark.h>
#include <nlohmann/json.hpp>

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;
using json = nlohmann::json;

static double elapsed(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}

static void guard() {
    const char* target = std::getenv("EXECUTION_TARGET");
    const char* enabled = std::getenv("ENABLE_SLAM");
    if (!target || (std::string(target) != "aws" && std::string(target) != "lightning")
        || !enabled || std::string(enabled) != "true") {
        throw std::runtime_error("Hosted execution target and ENABLE_SLAM=true are required.");
    }
#ifndef __linux__
    throw std::runtime_error("Only hosted Linux execution is permitted.");
#endif
    std::ifstream release("/proc/sys/kernel/osrelease");
    std::string kernel;
    std::getline(release, kernel);
    std::transform(kernel.begin(), kernel.end(), kernel.begin(), [](unsigned char c) { return std::tolower(c); });
    if (kernel.find("microsoft") != std::string::npos) {
        throw std::runtime_error("WSL backend execution is disabled.");
    }
}

int main(int argc, char** argv) {
    try {
        std::map<std::string, std::string> args;
        for (int i = 1; i < argc; ++i) {
            const std::string key = argv[i];
            if (key == "--no-viewer") continue;
            if (key == "--version") {
                std::cout << "slam_runner stella_vslam " << STELLA_COMMIT << " + offline-drain.patch\n";
                return 0;
            }
            if (i + 1 >= argc || key.rfind("--", 0) != 0) throw std::runtime_error("Invalid arguments");
            const std::set<std::string> valid{"--video", "--config", "--vocab", "--output", "--drain-timeout"};
            if (!valid.count(key) || args.count(key)) throw std::runtime_error("Unknown or repeated argument: " + key);
            args[key] = argv[++i];
        }
        for (const auto* key : {"--video", "--config", "--vocab", "--output"}) {
            if (!args.count(key)) throw std::runtime_error(std::string("Missing ") + key);
        }
        guard();
        const auto total_start = Clock::now();
        const fs::path output(args.at("--output"));
        fs::create_directories(output);
        auto cfg = std::make_shared<stella_vslam::config>(args.at("--config"));
        const auto camera = YAML::LoadFile(args.at("--config"))["Camera"];
        const double fps = camera["fps"].as<double>();
        const int width = camera["cols"].as<int>(), height = camera["rows"].as<int>();
        if (!std::isfinite(fps) || fps <= 0 || width < 16 || height < 16)
            throw std::runtime_error("Invalid camera geometry");
        cv::VideoCapture capture(args.at("--video"), cv::CAP_FFMPEG);
        if (!capture.isOpened()) throw std::runtime_error("Cannot decode video");
        // The shared Python preprocessing stage resolves VFR, rotation and resize.
        capture.set(cv::CAP_PROP_ORIENTATION_AUTO, 0);
        cv::setNumThreads(1);
        auto slam = std::make_unique<stella_vslam::system>(cfg, args.at("--vocab"));
        const double startup_seconds = elapsed(total_start);
        slam->startup();
        slam->enable_mapping_module();
        slam->enable_loop_detector();
        bool started = true;
        try {
            const auto track_start = Clock::now();
            std::size_t frames = 0, tracked = 0;
            double feed_seconds = 0, decode_seconds = 0;
            cv::Mat frame;
            while (true) {
                const auto decode_start = Clock::now();
                const bool decoded = capture.read(frame);
                decode_seconds += elapsed(decode_start);
                if (!decoded) break;
                if (frame.empty() || frame.cols != width || frame.rows != height)
                    throw std::runtime_error("Frame geometry differs from calibrated, normalized video");
                const auto feed_start = Clock::now();
                auto pose = slam->feed_monocular_frame(frame, static_cast<double>(frames) / fps);
                feed_seconds += elapsed(feed_start);
                if (pose && pose->allFinite()) ++tracked;
                ++frames;
            }
            const double tracking_wall_seconds = elapsed(track_start);
            const double drain_timeout = args.count("--drain-timeout") ? std::stod(args.at("--drain-timeout")) : 30;
            if (!std::isfinite(drain_timeout) || drain_timeout <= 0 || drain_timeout > 300)
                throw std::runtime_error("Invalid drain timeout");
            const auto drain_start = Clock::now();
            if (!slam->wait_for_pending_work(drain_timeout)) {
                // No apparently successful artifact may be exported with pending correction.
                throw std::runtime_error("Optimization did not drain before deadline");
            }
            const double drain_seconds = elapsed(drain_start);
            slam->shutdown();
            started = false;
            const auto export_start = Clock::now();
            // Engine recomposes frame poses from the corrected reference keyframes.
            slam->save_frame_trajectory((output / "trajectory.tum").string(), "TUM");
            slam->save_keyframe_trajectory((output / "keyframes.tum").string(), "TUM");
            std::vector<std::shared_ptr<stella_vslam::data::keyframe>> keyframes;
            auto publisher = slam->get_map_publisher();
            publisher->get_keyframes(keyframes);
            std::vector<std::shared_ptr<stella_vslam::data::landmark>> landmarks;
            std::set<std::shared_ptr<stella_vslam::data::landmark>> local;
            publisher->get_landmarks(landmarks, local);
            std::sort(landmarks.begin(), landmarks.end(), [](const auto& a, const auto& b) { return a->id_ < b->id_; });
            std::set<std::pair<unsigned int, unsigned int>> loop_edges;
            std::set<unsigned int> map_roots;
            std::size_t surviving_keyframes = 0;
            for (const auto& k : keyframes) {
                if (!k || k->will_be_erased()) continue;
                ++surviving_keyframes;
                map_roots.insert(k->graph_node_->get_spanning_root()->id_);
                for (const auto& other : k->graph_node_->get_loop_edges()) {
                    loop_edges.emplace(std::min(k->id_, other->id_), std::max(k->id_, other->id_));
                }
            }
            std::vector<std::array<double, 3>> points;
            std::ofstream csv(output / "landmarks.csv");
            csv.exceptions(std::ios::badbit | std::ios::failbit);
            csv << "x,y,z,observations\n" << std::setprecision(12);
            for (const auto& lm : landmarks) {
                if (!lm || lm->will_be_erased() || lm->num_observations() < 2) continue;
                const auto p = lm->get_pos_in_world();
                if (!p.allFinite()) continue;
                points.push_back({p.x(), p.y(), p.z()});
                csv << p.x() << ',' << p.y() << ',' << p.z() << ',' << lm->num_observations() << '\n';
            }
            csv.close();
            std::ofstream ply(output / "pointcloud.ply");
            ply.exceptions(std::ios::badbit | std::ios::failbit);
            ply << "ply\nformat ascii 1.0\ncomment relative arbitrary scale\nelement vertex " << points.size()
                << "\nproperty double x\nproperty double y\nproperty double z\nend_header\n" << std::setprecision(12);
            for (const auto& p : points) ply << p[0] << ' ' << p[1] << ' ' << p[2] << '\n';
            ply.close();
            const double export_seconds = elapsed(export_start);
            const bool success = frames > 0 && tracked >= 3 && points.size() >= 10
                && surviving_keyframes >= 2 && map_roots.size() == 1;
            json stats{
                {"status", success ? "success" : "failed"},
                {"engine_commit", STELLA_COMMIT}, {"engine_patch", "offline-drain.patch"},
                {"frames_processed", frames}, {"frames_tracked", tracked},
                {"processed_fps", fps}, {"keyframes", surviving_keyframes},
                {"raw_map_points", landmarks.size()}, {"map_points", points.size()},
                {"loop_edges", loop_edges.size()}, {"optimization_complete", true},
                {"map_components", map_roots.size()},
                {"pose_convention", "Twc"}, {"scale", "arbitrary"},
                {"startup_seconds", startup_seconds}, {"decode_seconds", decode_seconds},
                {"feed_seconds", feed_seconds}, {"tracking_wall_seconds", tracking_wall_seconds},
                {"optimization_drain_seconds", drain_seconds}, {"export_seconds", export_seconds},
                {"runner_seconds", elapsed(total_start)}
            };
            std::ofstream stats_file(output / "stats.json");
            stats_file.exceptions(std::ios::badbit | std::ios::failbit);
            stats_file << stats.dump(2) << '\n';
            return success ? 0 : 2;
        } catch (...) {
            if (started) { slam->abort_loop_BA(); slam->shutdown(); }
            throw;
        }
    } catch (const std::exception& e) {
        std::cerr << "slam_runner: " << e.what() << '\n';
        return 1;
    }
}
