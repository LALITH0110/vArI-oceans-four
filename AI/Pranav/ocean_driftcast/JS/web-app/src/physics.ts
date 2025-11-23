/**
 * Ocean Physics Engine
 *
 * Synthetic kinematic model of North Atlantic circulation.
 * Includes: subtropical gyre, Gulf Stream, North Atlantic Current, windage, diffusion.
 *
 * NOT FOR SCIENTIFIC USE - Presentation demo only.
 */

export interface VelocityField {
  u: Float32Array; // zonal (east-west) m/s
  v: Float32Array; // meridional (north-south) m/s
}

export interface Position {
  lat: number;
  lon: number;
}

export class OceanPhysics {
  // RNG seed
  private seed: number;
  private rngState: number;

  // Gyre parameters
  private gyreCenterLat = 30.0;
  private gyreCenterLon = -40.0;
  private gyreRadius = 20.0;
  private gyreStrength = 0.5; // m/s

  // Gulf Stream parameters
  private gulfStreamStrength = 2.0; // m/s
  private gulfStreamWidth = 2.0; // degrees

  // Windage parameters
  private windageFraction = 0.03;
  private windU = -5.0; // m/s
  private windV = 2.0; // m/s

  // Diffusion parameters
  private diffusionCoefficient = 100.0; // m^2/s

  // Beaching parameters
  public beachProbability = 0.15; // per week near shore
  public beachDistanceKm = 15.0; // km from coast
  public beachMinWeeks = 4; // minimum 4 weeks before beaching

  // Time step (weekly)
  private dt = 7 * 24 * 3600; // seconds

  // Constants
  private earthRadius = 6371000.0; // meters
  private degToRad = Math.PI / 180.0;
  private degToKm = 111.32; // km per degree latitude

  constructor(seed: number = 42) {
    this.seed = seed;
    this.rngState = seed;
    console.log('✓ PHYSICS READY');
  }

  /**
   * Simple LCG random number generator for reproducibility
   */
  private random(): number {
    this.rngState = (this.rngState * 1664525 + 1013904223) >>> 0;
    return (this.rngState / 4294967296);
  }

  /**
   * Normal distribution (Box-Muller transform)
   */
  private randomNormal(mean: number = 0, stdDev: number = 1): number {
    const u1 = this.random();
    const u2 = this.random();
    const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return mean + z0 * stdDev;
  }

  /**
   * Compute ocean velocity at given positions
   */
  velocityField(lats: Float32Array, lons: Float32Array): VelocityField {
    const n = lats.length;
    const u = new Float32Array(n);
    const v = new Float32Array(n);

    for (let i = 0; i < n; i++) {
      const lat = lats[i];
      const lon = lons[i];

      // 1. Subtropical gyre (clockwise)
      const { u: uGyre, v: vGyre } = this.gyreVelocity(lat, lon);
      u[i] += uGyre;
      v[i] += vGyre;

      // 2. Gulf Stream
      const { u: uGulf, v: vGulf } = this.gulfStreamVelocity(lat, lon);
      u[i] += uGulf;
      v[i] += vGulf;

      // 3. North Atlantic Current
      const { u: uNac, v: vNac } = this.northAtlanticCurrent(lat, lon);
      u[i] += uNac;
      v[i] += vNac;

      // 4. Windage
      const { u: uWind, v: vWind } = this.windage(lat, lon);
      u[i] += uWind;
      v[i] += vWind;
    }

    return { u, v };
  }

  /**
   * Clockwise subtropical gyre circulation
   */
  private gyreVelocity(lat: number, lon: number): { u: number; v: number } {
    const dlat = lat - this.gyreCenterLat;
    const dlon = lon - this.gyreCenterLon;
    const r = Math.sqrt(dlat * dlat + dlon * dlon) / this.gyreRadius;
    const vmag = this.gyreStrength * Math.exp(-r * r);
    const angle = Math.atan2(dlat, dlon);

    const u = -vmag * Math.sin(angle); // Clockwise
    const v = vmag * Math.cos(angle);

    return { u, v };
  }

  /**
   * Gulf Stream along US east coast
   */
  private gulfStreamVelocity(lat: number, lon: number): { u: number; v: number } {
    let u = 0;
    let v = 0;

    // Southern section (25N-35N)
    if (lat >= 25 && lat <= 35 && lon >= -80 && lon <= -70) {
      const distSouth = Math.abs(lon + 75);
      const profileSouth = Math.exp(-(distSouth / this.gulfStreamWidth) ** 2);
      v += this.gulfStreamStrength * profileSouth;
      u += 0.3 * this.gulfStreamStrength * profileSouth;
    }

    // Northern section (35N-42N)
    if (lat >= 35 && lat <= 42 && lon >= -75 && lon <= -65) {
      const centerLon = -75 + (lat - 35) * (10 / 7);
      const distNorth = Math.abs(lon - centerLon);
      const profileNorth = Math.exp(-(distNorth / this.gulfStreamWidth) ** 2);
      v += 0.7 * this.gulfStreamStrength * profileNorth;
      u += 1.5 * this.gulfStreamStrength * profileNorth;
    }

    return { u, v };
  }

  /**
   * North Atlantic Current toward Europe
   */
  private northAtlanticCurrent(lat: number, lon: number): { u: number; v: number } {
    let u = 0;
    let v = 0;

    if (lat >= 40 && lat <= 55 && lon >= -50 && lon <= -10) {
      const latCenter = 47.0;
      const latProfile = Math.exp(-((lat - latCenter) / 5.0) ** 2);
      u += 0.8 * this.gulfStreamStrength * latProfile;
      v += 0.1 * this.gulfStreamStrength * latProfile;
    }

    return { u, v };
  }

  /**
   * Windage from trade winds (10N-30N)
   */
  private windage(lat: number, lon: number): { u: number; v: number } {
    let weight = 0;

    if (lat >= 10 && lat <= 30) {
      weight = 1.0 - Math.abs(lat - 20) / 10.0;
      weight = Math.max(weight, 0.0);
    }

    const u = this.windageFraction * this.windU * weight;
    const v = this.windageFraction * this.windV * weight;

    return { u, v };
  }

  /**
   * Diffusion step (random walk)
   */
  diffusionStep(n: number): { du: Float32Array; dv: Float32Array } {
    const sigma = Math.sqrt(2 * this.diffusionCoefficient * this.dt);
    const du = new Float32Array(n);
    const dv = new Float32Array(n);

    for (let i = 0; i < n; i++) {
      du[i] = this.randomNormal(0, sigma);
      dv[i] = this.randomNormal(0, sigma);
    }

    return { du, dv };
  }

  /**
   * Convert meters to degrees
   */
  metersToDegrees(lats: Float32Array, dxM: Float32Array, dyM: Float32Array): { dlon: Float32Array; dlat: Float32Array } {
    const n = lats.length;
    const dlat = new Float32Array(n);
    const dlon = new Float32Array(n);

    for (let i = 0; i < n; i++) {
      dlat[i] = dyM[i] / (this.earthRadius * this.degToRad);
      const latRad = lats[i] * this.degToRad;
      dlon[i] = dxM[i] / (this.earthRadius * Math.cos(latRad) * this.degToRad + 1e-10);
    }

    return { dlon, dlat };
  }

  /**
   * Land mask for North Atlantic basin
   */
  isOnLand(lats: Float32Array, lons: Float32Array): Uint8Array {
    const n = lats.length;
    const onLand = new Uint8Array(n);

    for (let i = 0; i < n; i++) {
      const lat = lats[i];
      const lon = lons[i];

      // North America - west of east coast
      if (lat >= 25 && lat <= 60) {
        const eastCoastLon = this.interpolate(lat,
          [25, 30, 35, 40, 45, 50, 55, 60],
          [-80.5, -81.5, -77.0, -75.5, -68.0, -61.0, -58.0, -56.0]
        );
        if (lon < eastCoastLon) {
          onLand[i] = 1;
          continue;
        }
      }

      // Europe and Africa - east of west coast
      if (lat >= 10 && lat <= 60) {
        const westCoastLon = this.interpolate(lat,
          [10, 20, 30, 35, 40, 45, 50, 55, 60],
          [-17, -16, -9, -9, -9, -2, -5, -7, -10]
        );
        if (lon > (westCoastLon + 0.2)) {
          onLand[i] = 1;
          continue;
        }
      }

      // Mediterranean
      if (lat >= 30 && lat <= 46 && lon >= 0 && lon <= 36) {
        onLand[i] = 1;
        continue;
      }

      // Caribbean
      if (lat >= 10 && lat <= 25 && lon >= -85 && lon <= -60) {
        onLand[i] = 1;
        continue;
      }
    }

    return onLand;
  }

  /**
   * Linear interpolation
   */
  private interpolate(x: number, xp: number[], fp: number[]): number {
    if (x <= xp[0]) return fp[0];
    if (x >= xp[xp.length - 1]) return fp[fp.length - 1];

    for (let i = 0; i < xp.length - 1; i++) {
      if (x >= xp[i] && x <= xp[i + 1]) {
        const t = (x - xp[i]) / (xp[i + 1] - xp[i]);
        return fp[i] + t * (fp[i + 1] - fp[i]);
      }
    }

    return fp[fp.length - 1];
  }

  /**
   * Distance to nearest coast (km)
   */
  distanceToCoastKm(lats: Float32Array, lons: Float32Array): Float32Array {
    const n = lats.length;
    const minDist = new Float32Array(n);
    minDist.fill(999.0);

    // Sample points at various offsets
    const offsets = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3];

    for (const dlat of offsets) {
      for (const dlon of offsets) {
        if (dlat === 0 && dlon === 0) continue;

        const checkLats = new Float32Array(n);
        const checkLons = new Float32Array(n);

        for (let i = 0; i < n; i++) {
          checkLats[i] = lats[i] + dlat;
          checkLons[i] = lons[i] + dlon;
        }

        const onLand = this.isOnLand(checkLats, checkLons);
        const distDeg = Math.sqrt(dlat * dlat + dlon * dlon);
        const distKm = distDeg * this.degToKm;

        for (let i = 0; i < n; i++) {
          if (onLand[i] === 1) {
            minDist[i] = Math.min(minDist[i], distKm);
          }
        }
      }
    }

    return minDist;
  }

  /**
   * Check beaching (probabilistic near shore after minimum time)
   */
  checkBeaching(lats: Float32Array, lons: Float32Array, isBeached: Uint8Array, stepNumber: number): Uint8Array {
    const n = lats.length;
    const newBeached = new Uint8Array(isBeached);

    // No beaching before minimum time
    if (stepNumber < this.beachMinWeeks) {
      return newBeached;
    }

    // Find active particles
    const activeLats: number[] = [];
    const activeLons: number[] = [];
    const activeIndices: number[] = [];

    for (let i = 0; i < n; i++) {
      if (isBeached[i] === 0) {
        activeLats.push(lats[i]);
        activeLons.push(lons[i]);
        activeIndices.push(i);
      }
    }

    if (activeLats.length === 0) return newBeached;

    // Check distance to coast
    const activeLatsArray = new Float32Array(activeLats);
    const activeLonsArray = new Float32Array(activeLons);
    const distToCoast = this.distanceToCoastKm(activeLatsArray, activeLonsArray);

    // Probabilistic beaching for particles near coast
    for (let i = 0; i < activeLats.length; i++) {
      const nearCoast = distToCoast[i] <= this.beachDistanceKm;
      const beachRoll = this.random();

      if (nearCoast && beachRoll < this.beachProbability) {
        newBeached[activeIndices[i]] = 1;
      }
    }

    return newBeached;
  }

  /**
   * RK4 integration step
   */
  rk4Step(lats: Float32Array, lons: Float32Array, isBeached: Uint8Array): { lats: Float32Array; lons: Float32Array } {
    const n = lats.length;
    const newLats = new Float32Array(lats);
    const newLons = new Float32Array(lons);

    // Find active particles
    const activeLats: number[] = [];
    const activeLons: number[] = [];
    const activeIndices: number[] = [];

    for (let i = 0; i < n; i++) {
      if (isBeached[i] === 0) {
        activeLats.push(lats[i]);
        activeLons.push(lons[i]);
        activeIndices.push(i);
      }
    }

    if (activeLats.length === 0) return { lats: newLats, lons: newLons };

    const nActive = activeLats.length;
    const latActive = new Float32Array(activeLats);
    const lonActive = new Float32Array(activeLons);

    // K1
    const vel1 = this.velocityField(latActive, lonActive);
    const diff1 = this.diffusionStep(nActive);
    const dx1 = new Float32Array(nActive);
    const dy1 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      dx1[i] = vel1.u[i] * this.dt + diff1.du[i];
      dy1[i] = vel1.v[i] * this.dt + diff1.dv[i];
    }
    const deg1 = this.metersToDegrees(latActive, dx1, dy1);

    // K2
    const lat2 = new Float32Array(nActive);
    const lon2 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      lat2[i] = latActive[i] + 0.5 * deg1.dlat[i];
      lon2[i] = lonActive[i] + 0.5 * deg1.dlon[i];
    }
    const vel2 = this.velocityField(lat2, lon2);
    const diff2 = this.diffusionStep(nActive);
    const dx2 = new Float32Array(nActive);
    const dy2 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      dx2[i] = vel2.u[i] * this.dt + diff2.du[i];
      dy2[i] = vel2.v[i] * this.dt + diff2.dv[i];
    }
    const deg2 = this.metersToDegrees(lat2, dx2, dy2);

    // K3
    const lat3 = new Float32Array(nActive);
    const lon3 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      lat3[i] = latActive[i] + 0.5 * deg2.dlat[i];
      lon3[i] = lonActive[i] + 0.5 * deg2.dlon[i];
    }
    const vel3 = this.velocityField(lat3, lon3);
    const diff3 = this.diffusionStep(nActive);
    const dx3 = new Float32Array(nActive);
    const dy3 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      dx3[i] = vel3.u[i] * this.dt + diff3.du[i];
      dy3[i] = vel3.v[i] * this.dt + diff3.dv[i];
    }
    const deg3 = this.metersToDegrees(lat3, dx3, dy3);

    // K4
    const lat4 = new Float32Array(nActive);
    const lon4 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      lat4[i] = latActive[i] + deg3.dlat[i];
      lon4[i] = lonActive[i] + deg3.dlon[i];
    }
    const vel4 = this.velocityField(lat4, lon4);
    const diff4 = this.diffusionStep(nActive);
    const dx4 = new Float32Array(nActive);
    const dy4 = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      dx4[i] = vel4.u[i] * this.dt + diff4.du[i];
      dy4[i] = vel4.v[i] * this.dt + diff4.dv[i];
    }
    const deg4 = this.metersToDegrees(lat4, dx4, dy4);

    // Combine
    const dlon = new Float32Array(nActive);
    const dlat = new Float32Array(nActive);
    for (let i = 0; i < nActive; i++) {
      dlon[i] = (deg1.dlon[i] + 2 * deg2.dlon[i] + 2 * deg3.dlon[i] + deg4.dlon[i]) / 6.0;
      dlat[i] = (deg1.dlat[i] + 2 * deg2.dlat[i] + 2 * deg3.dlat[i] + deg4.dlat[i]) / 6.0;
    }

    // Update positions
    for (let i = 0; i < nActive; i++) {
      const idx = activeIndices[i];
      newLats[idx] = lats[idx] + dlat[i];
      newLons[idx] = lons[idx] + dlon[i];

      // Bounds
      newLats[idx] = Math.max(-90, Math.min(90, newLats[idx]));
      if (newLons[idx] < -180) newLons[idx] += 360;
      if (newLons[idx] > 180) newLons[idx] -= 360;
    }

    return { lats: newLats, lons: newLons };
  }

  /**
   * Spawn particles offshore (ensuring ocean start)
   */
  spawnOffshore(centerLat: number, centerLon: number, nParticles: number, radiusKm: number = 20.0): { lats: Float32Array; lons: Float32Array } {
    const radiusDeg = radiusKm / this.degToKm;
    const latList: number[] = [];
    const lonList: number[] = [];

    let attempts = 0;
    const maxAttempts = nParticles * 10;

    while (latList.length < nParticles && attempts < maxAttempts) {
      const needed = nParticles - latList.length;
      const angles: number[] = [];
      const radii: number[] = [];

      for (let i = 0; i < needed; i++) {
        angles.push(this.random() * 2 * Math.PI);
        radii.push(this.random() * radiusDeg);
      }

      const candidateLats = new Float32Array(needed);
      const candidateLons = new Float32Array(needed);

      for (let i = 0; i < needed; i++) {
        const dlat = radii[i] * Math.cos(angles[i]);
        const dlon = radii[i] * Math.sin(angles[i]) / Math.cos(centerLat * this.degToRad);
        candidateLats[i] = centerLat + dlat;
        candidateLons[i] = centerLon + dlon;
      }

      const inOcean = this.isOnLand(candidateLats, candidateLons);

      for (let i = 0; i < needed; i++) {
        if (inOcean[i] === 0) {
          latList.push(candidateLats[i]);
          lonList.push(candidateLons[i]);
        }
      }

      attempts++;
    }

    return {
      lats: new Float32Array(latList.slice(0, nParticles)),
      lons: new Float32Array(lonList.slice(0, nParticles))
    };
  }
}
