/**
 * Ocean DriftCast - Main App Component
 *
 * Production-grade particle drift visualization for North Atlantic basin.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { OceanPhysics } from './physics';
import { ParticleSystem, CityData, createParticleSystemFromCity, Trajectory } from './particles';
import { MapView } from './components/MapView';
import { CityCombobox } from './components/CityCombobox';
import { Controls } from './components/Controls';
import { InfoCard } from './components/InfoCard';
import './styles/app.css';

export function App() {
  // Physics engine (singleton)
  const physicsRef = useRef<OceanPhysics | null>(null);
  const [physicsReady, setPhysicsReady] = useState(false);

  // City data
  const [cities, setCities] = useState<CityData[]>([]);
  const [selectedCity, setSelectedCity] = useState<CityData | null>(null);

  // Simulation state
  const [particleSystem, setParticleSystem] = useState<ParticleSystem | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState(0);

  // Playback state
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [visualizationMode, setVisualizationMode] = useState<'single' | 'particles'>('single');

  // Trajectory data
  const [trajectory, setTrajectory] = useState<Trajectory | null>(null);
  const [maxSteps, setMaxSteps] = useState(1040); // 20 years

  // Initialize physics
  useEffect(() => {
    if (!physicsRef.current) {
      physicsRef.current = new OceanPhysics(42);
      setPhysicsReady(true);
    }
  }, []);

  // Load cities
  useEffect(() => {
    fetch('/seeds.json')
      .then(res => res.json())
      .then(data => {
        setCities(data);
        console.log('✓ DATA READY -', data.length, 'cities loaded');
      })
      .catch(err => console.error('Failed to load cities:', err));
  }, []);

  // Load city and run simulation
  const handleLoadCity = useCallback(async (city: CityData) => {
    if (!physicsRef.current) return;

    setSelectedCity(city);
    setIsSimulating(true);
    setSimulationProgress(0);
    setCurrentStep(0);
    setIsPlaying(false);
    setTrajectory(null);
    setParticleSystem(null);

    console.log(`\nLoading: ${city.city}`);

    // Run simulation in background
    setTimeout(() => {
      if (!physicsRef.current) return;

      const nParticles = visualizationMode === 'single' ? 100 : 2000;
      const ps = createParticleSystemFromCity(physicsRef.current, city, nParticles);

      console.log(`  Simulating ${maxSteps} weeks (${(maxSteps / 52).toFixed(1)} years) with ${nParticles} particles...`);

      // Simulate with progress updates
      const startTime = Date.now();
      ps.simulate(maxSteps, (step) => {
        setSimulationProgress((step / maxSteps) * 100);
      });
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      console.log(`  ✓ Simulation complete in ${elapsed}s`);

      // Get metrics
      const metrics = ps.getMetrics();
      const probCat = ps.getProbabilityCategory();

      console.log(`    Probability: ${probCat} (${(metrics.oceanReachProb * 100).toFixed(1)}%)`);
      console.log(`    Median distance: ${metrics.medianDistanceKm.toFixed(0)} km`);
      console.log(`    Beached: ${metrics.nBeached}/${metrics.nParticles}`);

      // Get trajectory
      const traj = visualizationMode === 'single'
        ? ps.getMeanTrajectory(1)
        : ps.getMeanTrajectory(1); // Still use mean for now

      setTrajectory(traj);
      setParticleSystem(ps);
      setIsSimulating(false);
      setSimulationProgress(100);
    }, 100);
  }, [maxSteps, visualizationMode]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !trajectory) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        const next = prev + speed;
        if (next >= (trajectory.lats.length - 1)) {
          setIsPlaying(false);
          return trajectory.lats.length - 1;
        }
        return next;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [isPlaying, speed, trajectory]);

  // UI ready check
  useEffect(() => {
    if (physicsReady && cities.length > 0) {
      console.log('✓ UI READY');
    }
  }, [physicsReady, cities]);

  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo">
          <h1>Ocean DriftCast</h1>
          <p className="subtitle">North Atlantic Particle Trajectories</p>
        </div>

        <CityCombobox
          cities={cities}
          onSelect={handleLoadCity}
          disabled={isSimulating}
        />

        {selectedCity && (
          <>
            <div className="mode-toggle">
              <label>Visualization Mode</label>
              <div className="toggle-buttons">
                <button
                  className={visualizationMode === 'single' ? 'active' : ''}
                  onClick={() => setVisualizationMode('single')}
                  disabled={isSimulating}
                >
                  Single Path
                </button>
                <button
                  className={visualizationMode === 'particles' ? 'active' : ''}
                  onClick={() => setVisualizationMode('particles')}
                  disabled={isSimulating}
                >
                  Particles
                </button>
              </div>
            </div>

            <Controls
              isPlaying={isPlaying}
              speed={speed}
              currentStep={currentStep}
              maxSteps={trajectory?.lats.length || maxSteps}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onReset={() => { setCurrentStep(0); setIsPlaying(false); }}
              onSpeedChange={setSpeed}
              onExportGIF={() => console.log('Export GIF')}
              onExportMP4={() => console.log('Export MP4')}
              disabled={!trajectory || isSimulating}
            />

            {particleSystem && (
              <InfoCard
                city={selectedCity.city}
                metrics={particleSystem.getMetrics()}
                probabilityCategory={particleSystem.getProbabilityCategory()}
                currentStep={currentStep}
                maxSteps={trajectory?.lats.length || maxSteps}
              />
            )}
          </>
        )}

        {isSimulating && (
          <div className="progress-container">
            <div className="progress-label">Simulating...</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${simulationProgress}%` }} />
            </div>
            <div className="progress-percent">{simulationProgress.toFixed(0)}%</div>
          </div>
        )}

        <div className="footer">
          <p className="disclaimer">Synthetic demo for presentation. Not scientific output.</p>
        </div>
      </div>

      {/* Main map view */}
      <div className="map-container">
        <MapView
          trajectory={trajectory}
          currentStep={currentStep}
          selectedCity={selectedCity}
        />

        {!selectedCity && (
          <div className="instruction-overlay">
            <div className="instruction-content">
              <h2>Pick a city to simulate a 20-year drift</h2>
              <p>Select from 25+ coastal and inland cities across North America, Europe, and Africa</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
