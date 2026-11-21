"""Run the Medusa BlazeFace model on a Windows camera."""

import argparse
from pathlib import Path

import cv2
import mediapipe as mp


def detect_faces(detector, frame):
    """Return detections in the original frame's pixel coordinates."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return detector.detect(image).detections


def draw_faces(frame, detections):
    height, width = frame.shape[:2]
    for detection in detections:
        box = detection.bounding_box
        left, top = box.origin_x, box.origin_y
        right, bottom = left + box.width, top + box.height
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        score = detection.categories[0].score
        cv2.putText(frame, f"{score:.2f}", (max(0, left), max(16, top - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        for point in detection.keypoints:
            cv2.circle(frame, (round(point.x * width), round(point.y * height)),
                       2, (0, 255, 255), -1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, required=True,
                        help="Windows camera index, usually 0 or 1")
    parser.add_argument("--model", type=Path,
                        default=Path(__file__).with_name("blaze_face_short_range.tflite"))
    args = parser.parse_args()
    if not args.model.is_file():
        parser.error(f"Face detector model not found: {args.model}")

    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        min_detection_confidence=0.5,
    )
    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    try:
        if not camera.isOpened():
            parser.exit(1, f"Could not open camera {args.camera}. Check the USB "
                           "connection and Windows camera permissions, or try another index.\n")
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        with mp.tasks.vision.FaceDetector.create_from_options(options) as detector:
            while True:
                ok, frame = camera.read()
                if not ok:
                    parser.exit(1, f"Camera {args.camera} stopped delivering frames.\n")
                draw_faces(frame, detect_faces(detector, frame))
                cv2.imshow("Medusa BlazeFace | Q to quit", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
