/**
 * Info Card Component
 *
 * Displays simulation metrics and probability category.
 */

import React from 'react';
import { Metrics } from '../particles';

interface InfoCardProps {
  city: string;
  metrics: Metrics;
  probabilityCategory: 'LOW' | 'MEDIUM' | 'HIGH';
  currentStep: number;
  maxSteps: number;
}

export const InfoCard: React.FC<InfoCardProps> = ({
  city,
  metrics,
  probabilityCategory,
  currentStep,
  maxSteps
}) => {
  const getCategoryColor = (category: 'LOW' | 'MEDIUM' | 'HIGH'): string => {
    switch (category) {
      case 'HIGH':
        return '#00d9ff';
      case 'MEDIUM':
        return '#ffd700';
      case 'LOW':
        return '#ff6b6b';
    }
  };

  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US', { maximumFractionDigits: 0 });
  };

  return (
    <div className="info-card">
      <div className="info-header">
        <h3 className="city-name">{city}</h3>
        <div
          className="probability-badge"
          style={{ borderColor: getCategoryColor(probabilityCategory) }}
        >
          <span style={{ color: getCategoryColor(probabilityCategory) }}>
            {probabilityCategory}
          </span>
        </div>
      </div>

      <div className="info-metrics">
        <div className="metric">
          <span className="metric-label">Ocean Reach</span>
          <span className="metric-value">
            {(metrics.oceanReachProb * 100).toFixed(1)}%
          </span>
        </div>

        <div className="metric">
          <span className="metric-label">Distance</span>
          <span className="metric-value">
            {formatNumber(metrics.medianDistanceKm)} km
          </span>
        </div>

        <div className="metric">
          <span className="metric-label">Beached</span>
          <span className="metric-value">
            {metrics.nBeached} / {metrics.nParticles}
          </span>
        </div>

        <div className="metric">
          <span className="metric-label">Duration</span>
          <span className="metric-value">
            {metrics.years.toFixed(1)} years
          </span>
        </div>
      </div>
    </div>
  );
};
