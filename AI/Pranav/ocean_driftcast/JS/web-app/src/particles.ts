/**
 * Particle System
 *
 * Manages particle trajectories over time with full history tracking.
 */

import { OceanPhysics } from './physics';

export interface CityData {
  city: string;
  lat: number;
  lon: number;
  type: 'coastal' | 'inland';
  region: string;
  outlet?: {
    name: string;
    lat: number;
    lon: number;
  };
}

export interface Metrics {
  nParticles: number;
  nBeached: number;
  nOcean: number;
  beachedFraction: number;
  oceanReachProb: number;
  medianDistanceKm: number;
  meanDistanceKm: number;
  maxDistanceKm: number;
  nSteps: number;
  years: number;
}

export interface Trajectory {
  lats: number[];
  lons: number[];
}

export class ParticleSystem {
  private physics: OceanPhysics;
  private nParticles: number;
  private releaseLat: number;
  private releaseLon: number;

  // Current state
  public lats: Float32Array;
  public lons: Float32Array;
  public isBeached: Uint8Array;

  // History
  public historyLats: Float32Array[] = [];
  public historyLons: Float32Array[] = [];
  public historyBeached: Uint8Array[] = [];

  // Metrics
  public stepCount = 0;
  private totalDistance: Float32Array;

  constructor(physics: OceanPhysics, nParticles: number, releaseLat: number, releaseLon: number, radiusKm: number = 20.0) {
    this.physics = physics;
    this.nParticles = nParticles;
    this.releaseLat = releaseLat;
    this.releaseLon = releaseLon;

    // Spawn offshore
    const spawn = physics.spawnOffshore(releaseLat, releaseLon, nParticles, radiusKm);
    this.lats = spawn.lats;
    this.lons = spawn.lons;

    // Verify spawn
    const onLand = physics.isOnLand(this.lats, this.lons);
    const nOnLand = onLand.reduce((sum, val) => sum + val, 0);
    if (nOnLand > 0) {
      console.warn(`WARNING: ${nOnLand}/${nParticles} particles spawned on land!`);
    }

    this.isBeached = new Uint8Array(nParticles);
    this.totalDistance = new Float32Array(nParticles);

    // Store initial state
    this.historyLats.push(new Float32Array(this.lats));
    this.historyLons.push(new Float32Array(this.lons));
    this.historyBeached.push(new Uint8Array(this.isBeached));
  }

  /**
   * Advance simulation by one time step
   */
  step(): void {
    // Store previous positions
    const prevLats = new Float32Array(this.lats);
    const prevLons = new Float32Array(this.lons);

    // RK4 integration
    const newPos = this.physics.rk4Step(this.lats, this.lons, this.isBeached);
    this.lats = newPos.lats;
    this.lons = newPos.lons;

    // Check beaching
    this.isBeached = this.physics.checkBeaching(this.lats, this.lons, this.isBeached, this.stepCount);

    // Calculate distance traveled
    for (let i = 0; i < this.nParticles; i++) {
      if (this.isBeached[i] === 0) {
        const dlat = this.lats[i] - prevLats[i];
        const dlon = this.lons[i] - prevLons[i];

        const latRad = prevLats[i] * Math.PI / 180;
        const dx = dlon * Math.cos(latRad) * 111.32; // km
        const dy = dlat * 111.32; // km
        const dist = Math.sqrt(dx * dx + dy * dy);

        this.totalDistance[i] += dist;
      }
    }

    // Store history
    this.historyLats.push(new Float32Array(this.lats));
    this.historyLons.push(new Float32Array(this.lons));
    this.historyBeached.push(new Uint8Array(this.isBeached));

    this.stepCount++;
  }

  /**
   * Run simulation for n steps
   */
  simulate(nSteps: number, progressCallback?: (step: number) => void): void {
    for (let i = 0; i < nSteps; i++) {
      this.step();

      if (progressCallback && i % 100 === 0) {
        progressCallback(i);
      }
    }
  }

  /**
   * Get metrics
   */
  getMetrics(): Metrics {
    const nBeached = this.isBeached.reduce((sum, val) => sum + val, 0);
    const nOcean = this.nParticles - nBeached;

    const oceanReachProb = nOcean / this.nParticles;

    const distances = Array.from(this.totalDistance);
    distances.sort((a, b) => a - b);

    const medianDistanceKm = distances[Math.floor(distances.length / 2)];
    const meanDistanceKm = distances.reduce((sum, d) => sum + d, 0) / distances.length;
    const maxDistanceKm = Math.max(...distances);

    return {
      nParticles: this.nParticles,
      nBeached,
      nOcean,
      beachedFraction: nBeached / this.nParticles,
      oceanReachProb,
      medianDistanceKm,
      meanDistanceKm,
      maxDistanceKm,
      nSteps: this.stepCount,
      years: this.stepCount / 52.0
    };
  }

  /**
   * Get probability category
   */
  getProbabilityCategory(): 'LOW' | 'MEDIUM' | 'HIGH' {
    const metrics = this.getMetrics();
    const prob = metrics.oceanReachProb;

    if (prob < 0.3) return 'LOW';
    if (prob < 0.6) return 'MEDIUM';
    return 'HIGH';
  }

  /**
   * Get trajectory arrays (one per particle)
   */
  getTrajectoryArrays(subsample: number = 1): Trajectory[] {
    const trajectories: Trajectory[] = [];

    for (let i = 0; i < this.nParticles; i++) {
      const lats: number[] = [];
      const lons: number[] = [];

      for (let t = 0; t < this.historyLats.length; t += subsample) {
        lats.push(this.historyLats[t][i]);
        lons.push(this.historyLons[t][i]);
      }

      trajectories.push({ lats, lons });
    }

    return trajectories;
  }

  /**
   * Get mean trajectory (for single path visualization)
   */
  getMeanTrajectory(subsample: number = 1): Trajectory {
    const lats: number[] = [];
    const lons: number[] = [];

    for (let t = 0; t < this.historyLats.length; t += subsample) {
      let sumLat = 0;
      let sumLon = 0;
      let count = 0;

      for (let i = 0; i < this.nParticles; i++) {
        if (this.historyBeached[t][i] === 0) {
          sumLat += this.historyLats[t][i];
          sumLon += this.historyLons[t][i];
          count++;
        }
      }

      if (count > 0) {
        lats.push(sumLat / count);
        lons.push(sumLon / count);
      }
    }

    return { lats, lons };
  }

  /**
   * Get positions at specific step
   */
  getPositionsAtStep(step: number): { lats: Float32Array; lons: Float32Array; beached: Uint8Array } {
    if (step < 0 || step >= this.historyLats.length) {
      throw new Error(`Step ${step} out of range [0, ${this.historyLats.length - 1}]`);
    }

    return {
      lats: this.historyLats[step],
      lons: this.historyLons[step],
      beached: this.historyBeached[step]
    };
  }
}

/**
 * Create particle system from city data
 */
export function createParticleSystemFromCity(physics: OceanPhysics, cityData: CityData, nParticles: number = 5000): ParticleSystem {
  let lat = cityData.lat;
  let lon = cityData.lon;
  let radiusKm = 20.0;

  // For inland cities, use ocean outlet
  if (cityData.type === 'inland' && cityData.outlet) {
    lat = cityData.outlet.lat;
    lon = cityData.outlet.lon;
    radiusKm = 30.0; // Larger spread for inland outlets
  }

  return new ParticleSystem(physics, nParticles, lat, lon, radiusKm);
}
