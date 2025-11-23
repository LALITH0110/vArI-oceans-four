/**
 * Controls Component
 *
 * Playback controls: Play, Pause, Reset, Speed, Export GIF/MP4.
 */

import React from 'react';

interface ControlsProps {
  isPlaying: boolean;
  speed: number;
  currentStep: number;
  maxSteps: number;
  onPlay: () => void;
  onPause: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
  onExportGIF: () => void;
  onExportMP4: () => void;
  disabled?: boolean;
}

export const Controls: React.FC<ControlsProps> = ({
  isPlaying,
  speed,
  currentStep,
  maxSteps,
  onPlay,
  onPause,
  onReset,
  onSpeedChange,
  onExportGIF,
  onExportMP4,
  disabled = false
}) => {
  const handleSpeedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSpeedChange(Number(e.target.value));
  };

  const getSpeedLabel = (speed: number): string => {
    if (speed === 1) return '1x';
    if (speed === 5) return '5x';
    if (speed === 20) return '20x';
    return `${speed}x`;
  };

  return (
    <div className="controls">
      <div className="playback-controls">
        <button
          className="control-button"
          onClick={isPlaying ? onPause : onPlay}
          disabled={disabled}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <span className="icon">⏸</span>
          ) : (
            <span className="icon">▶</span>
          )}
          <span className="label">{isPlaying ? 'Pause' : 'Play'}</span>
        </button>

        <button
          className="control-button"
          onClick={onReset}
          disabled={disabled}
          aria-label="Reset"
        >
          <span className="icon">⏮</span>
          <span className="label">Reset</span>
        </button>
      </div>

      <div className="speed-control">
        <label>Speed</label>
        <div className="speed-slider-container">
          <input
            type="range"
            min="1"
            max="20"
            value={speed}
            onChange={handleSpeedChange}
            disabled={disabled}
            className="speed-slider"
            list="speed-markers"
          />
          <datalist id="speed-markers">
            <option value="1"></option>
            <option value="5"></option>
            <option value="20"></option>
          </datalist>
          <div className="speed-label">{getSpeedLabel(speed)}</div>
        </div>
      </div>

      <div className="export-controls">
        <label>Export</label>
        <div className="export-buttons">
          <button
            className="export-button"
            onClick={onExportGIF}
            disabled={disabled}
          >
            <span className="icon">📷</span>
            Save GIF
          </button>
          <button
            className="export-button"
            onClick={onExportMP4}
            disabled={disabled}
          >
            <span className="icon">🎥</span>
            Save MP4
          </button>
        </div>
      </div>

      <div className="time-display">
        <div className="time-label">Week {currentStep} of {maxSteps}</div>
        <div className="time-bar">
          <div
            className="time-progress"
            style={{ width: `${(currentStep / maxSteps) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};
