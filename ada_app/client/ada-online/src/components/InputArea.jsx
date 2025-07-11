// src/components/InputArea.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './InputArea.css'; // Make sure to add styles for the new button here too

/**
 * Renders the text input, send button, mute/unmute button, and webcam button.
 * Handles user input and interactions, communicating via callbacks.
 * @param {object} props - Component props.
 * @param {function} props.onSendText - Callback when text is sent.
 * @param {boolean} props.isMuted - Whether the mic is currently muted.
 * @param {boolean} props.isListening - Whether the mic is actively listening.
 * @param {function} props.onToggleMute - Callback when mute/unmute button is clicked.
 * @param {boolean} props.micSupported - Whether the browser supports Web Speech API.
 * @param {boolean} props.isVideoFeedVisible - Whether the video feed (webcam or screen) is currently visible.
 * @param {function} props.onToggleVideoFeed - Callback when video feed toggle button is clicked.
 */
function InputArea({
    onSendText,
    isMuted,
    isListening,
    onToggleMute,
    micSupported,
    isVideoFeedVisible, // **** RECEIVE VIDEO FEED PROP ****
    onToggleVideoFeed   // **** RECEIVE VIDEO FEED HANDLER ****
}) {
    const [inputValue, setInputValue] = useState('');

    // Handle changes in the text input field
    const handleInputChange = (event) => {
        setInputValue(event.target.value);
    };

    // Handle sending text (button click or Enter key)
    const handleSend = () => {
        const trimmedInput = inputValue.trim();
        if (trimmedInput) {
            onSendText(trimmedInput); // Call parent handler
            setInputValue(''); // Clear the input field
        }
    };

    // Handle Enter key press in the input field
    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent potential form submission/newline
            handleSend();
        }
    };

    // Determine Mute button text and appearance
     let muteButtonText = 'Mic N/A';
     let muteButtonClass = 'mute-button';
     let isMuteButtonDisabled = true;

     if (micSupported) {
         isMuteButtonDisabled = false;
         if (isMuted) {
             muteButtonText = 'Unmute';
             muteButtonClass += ' muted'; // Add 'muted' class for styling
         } else {
              // You could optionally show "Listening..." if isListening is true
              // muteButtonText = isListening ? 'Listening...' : 'Mute';
              muteButtonText = 'Mute'; // Keep it simple like original for now
         }
     }

    // **** DETERMINE VIDEO FEED BUTTON TEXT/STYLE ****
    const videoFeedButtonText = isVideoFeedVisible ? 'Hide Video' : 'Show Video';
    const videoFeedButtonClass = `video-feed-button ${isVideoFeedVisible ? 'active' : ''}`;


    return (
        <div className="input-area">
            <input
                type="text"
                id="message-input" // Keep original ID if needed, though less common in React
                className="message-input"
                placeholder="Type your message or use the mic..."
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyPress} // Use onKeyDown for better Enter key detection
                aria-label="Message Input"
            />
            <button
                className="send-button"
                onClick={handleSend}
                aria-label="Send Message"
            >
                Send
            </button>
            <button
                className={muteButtonClass}
                onClick={onToggleMute}
                disabled={isMuteButtonDisabled}
                aria-label={muteButtonText} // Good for accessibility
            >
                {muteButtonText}
            </button>
             {/* **** ADD VIDEO FEED TOGGLE BUTTON **** */}
            <button
                className={videoFeedButtonClass} // Add specific styles in InputArea.css
                onClick={onToggleVideoFeed}
                aria-label={videoFeedButtonText}
            >
                {videoFeedButtonText}
            </button>
        </div>
    );
}

InputArea.propTypes = {
    onSendText: PropTypes.func.isRequired,
    isMuted: PropTypes.bool.isRequired,
    isListening: PropTypes.bool.isRequired, // Include if used for styling/text
    onToggleMute: PropTypes.func.isRequired,
    micSupported: PropTypes.bool.isRequired,
    isVideoFeedVisible: PropTypes.bool.isRequired, // **** ADD VIDEO FEED PROP TYPE ****
    onToggleVideoFeed: PropTypes.func.isRequired,  // **** ADD VIDEO FEED HANDLER PROP TYPE ****
};

export default InputArea;
