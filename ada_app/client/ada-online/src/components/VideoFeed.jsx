// src/components/VideoFeed.jsx
import React, { useRef, useEffect, useState, useCallback } from "react";
import PropTypes from "prop-types";
import "./VideoFeed.css"; // Updated CSS import

function VideoFeed({ isVisible, onClose, socket }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [videoSource, setVideoSource] = useState("webcam"); // 'webcam' or 'screen'

  const captureAndSendFrame = useCallback(() => {
    if (
      !videoRef.current ||
      !canvasRef.current ||
      !socket?.current ||
      videoRef.current.readyState < videoRef.current.HAVE_METADATA
    ) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    const captureWidth = video.videoWidth;
    const captureHeight = video.videoHeight;
    if (canvas.width !== captureWidth) canvas.width = captureWidth;
    if (canvas.height !== captureHeight) canvas.height = captureHeight;

    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    try {
      const frameDataUrl = canvas.toDataURL("image/jpeg", 0.7);

      if (socket.current.connected) {
        socket.current.emit("send_video_frame", { frame: frameDataUrl });
      }
    } catch (e) {
      console.error("Error converting canvas to data URL:", e);
    }
  }, [socket]);

  const stopVideoStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      console.log("Video stream stopped.");
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      console.log("Frame capture interval cleared.");
    }
    setHasError(false);
    setErrorMessage("");
  }, []);

  const startVideoStream = useCallback(async () => {
    if (streamRef.current) return;

    setHasError(false);
    setErrorMessage("");
    console.log(`Attempting to start ${videoSource} stream...`);

    try {
      let stream;
      if (videoSource === "webcam") {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      } else if (videoSource === "screen") {
        stream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false, // Typically screen sharing doesn't include audio by default
        });
      } else {
        throw new Error("Invalid video source specified.");
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = async () => {
          try {
            await videoRef.current.play();
            console.log(`${videoSource} stream started and playing.`);
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = setInterval(captureAndSendFrame, 1000);
            console.log("Frame capture interval started.");
          } catch (playError) {
            console.error(`Error playing ${videoSource} stream:`, playError);
            setHasError(true);
            setErrorMessage(`Could not play ${videoSource} stream.`);
            stopVideoStream();
          }
        };
      } else {
        console.warn("Video element not available after getting stream...");
        stopVideoStream();
      }
    } catch (err) {
      console.error(`Error accessing ${videoSource}:`, err);
      setHasError(true);
      if (
        err.name === "NotAllowedError" ||
        err.name === "PermissionDeniedError"
      ) {
        setErrorMessage(`${videoSource} permission denied.`);
      } else if (
        err.name === "NotFoundError" ||
        err.name === "DevicesNotFoundError"
      ) {
        setErrorMessage(`No ${videoSource} found.`);
      } else if (err.name === "AbortError") {
        setErrorMessage("Screen sharing cancelled by user.");
      } else {
        setErrorMessage(`Could not access ${videoSource}. Error: ` + err.message);
      }
      stopVideoStream();
    }
  }, [videoSource, captureAndSendFrame, stopVideoStream]);

  useEffect(() => {
    if (!isVisible) {
      stopVideoStream();
      return;
    }

    startVideoStream();

    return () => {
      stopVideoStream();
    };
  }, [isVisible, startVideoStream, stopVideoStream]);

  const handleSourceChange = (source) => {
    if (videoSource !== source) {
      stopVideoStream(); // Stop current stream before changing source
      setVideoSource(source);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="video-feed-container">
      <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
      {hasError ? (
        <div className="video-error">
          <p>{errorMessage}</p>
          <button onClick={onClose} className="video-close-button error-close">
            Close
          </button>
        </div>
      ) : (
        <>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="video-element" // Changed class name
          ></video>
          <div className="video-controls">
            <button
              onClick={() => handleSourceChange("webcam")}
              className={`control-button ${videoSource === "webcam" ? "active" : ""}`}
            >
              Webcam
            </button>
            <button
              onClick={() => handleSourceChange("screen")}
              className={`control-button ${videoSource === "screen" ? "active" : ""}`}
            >
              Screen Share
            </button>
            <button
              onClick={onClose}
              className="video-close-button"
              aria-label="Close Video Feed"
            >
              ×
            </button>
          </div>
        </>
      )}
    </div>
  );
}

VideoFeed.propTypes = {
  isVisible: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  socket: PropTypes.object,
};

export default VideoFeed;
