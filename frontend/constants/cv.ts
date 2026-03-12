/**
 * All classes we can currently detect. Keep in sync with backend.
 * Used for the wrong detected item correction modal.
 */
export const CV_CLASSES = [
  "container",
  "electronics",
  "jackets",
  "pants",
  "shoes",
  "shorts",
  "tops",
];

/*
 * Minimum confidence score for a detection to not prompt a retake
 */
export const CONFIDENCE_THRESHOLD = 0.6;

export const CAMERA_CAPTURE_DELAY = 1500;
