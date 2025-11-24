/**
 * Smoke Test
 *
 * Basic verification that data loads and core logic works.
 */

const fs = require('fs');
const path = require('path');

console.log('============================================================');
console.log('  OCEAN DRIFTCAST - SMOKE TEST');
console.log('============================================================\n');

let passedTests = 0;
let totalTests = 0;

function test(name, fn) {
  totalTests++;
  try {
    fn();
    console.log(`✓ ${name}`);
    passedTests++;
  } catch (err) {
    console.log(`✗ ${name}`);
    console.log(`  Error: ${err.message}`);
  }
}

// Test 1: Verify seeds.json exists and is valid
test('Seeds.json exists and is valid JSON', () => {
  const seedsPath = path.join(__dirname, '../public/seeds.json');
  if (!fs.existsSync(seedsPath)) {
    throw new Error('seeds.json not found');
  }

  const data = JSON.parse(fs.readFileSync(seedsPath, 'utf8'));

  if (!Array.isArray(data)) {
    throw new Error('seeds.json is not an array');
  }

  if (data.length < 20) {
    throw new Error(`Expected 20+ cities, found ${data.length}`);
  }

  console.log(`  - Loaded ${data.length} cities`);
});

// Test 2: Verify seeds have required fields
test('All seeds have required fields', () => {
  const seedsPath = path.join(__dirname, '../public/seeds.json');
  const data = JSON.parse(fs.readFileSync(seedsPath, 'utf8'));

  const requiredFields = ['city', 'lat', 'lon', 'type', 'region'];

  data.forEach((city, index) => {
    requiredFields.forEach(field => {
      if (!(field in city)) {
        throw new Error(`City at index ${index} missing field: ${field}`);
      }
    });

    if (!['coastal', 'inland'].includes(city.type)) {
      throw new Error(`City at index ${index} has invalid type: ${city.type}`);
    }
  });

  console.log(`  - All ${data.length} cities valid`);
});

// Test 3: Verify inland cities have outlets
test('Inland cities have outlet data', () => {
  const seedsPath = path.join(__dirname, '../public/seeds.json');
  const data = JSON.parse(fs.readFileSync(seedsPath, 'utf8'));

  const inlandCities = data.filter(c => c.type === 'inland');

  if (inlandCities.length === 0) {
    console.log('  - No inland cities to test');
    return;
  }

  inlandCities.forEach(city => {
    if (!city.outlet) {
      throw new Error(`Inland city "${city.city}" missing outlet data`);
    }

    if (!city.outlet.lat || !city.outlet.lon) {
      throw new Error(`Inland city "${city.city}" outlet missing lat/lon`);
    }
  });

  console.log(`  - ${inlandCities.length} inland cities have outlets`);
});

// Test 4: Verify package.json has correct scripts
test('Package.json has required scripts', () => {
  const pkgPath = path.join(__dirname, '../package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

  const requiredScripts = ['dev', 'build', 'preview'];

  requiredScripts.forEach(script => {
    if (!pkg.scripts[script]) {
      throw new Error(`Missing script: ${script}`);
    }
  });

  console.log('  - All required scripts present');
});

// Test 5: Verify core dependencies
test('Core dependencies installed', () => {
  const pkgPath = path.join(__dirname, '../package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

  const requiredDeps = [
    'react',
    'react-dom',
    'maplibre-gl',
    'react-map-gl',
    'fuse.js'
  ];

  requiredDeps.forEach(dep => {
    if (!pkg.dependencies[dep]) {
      throw new Error(`Missing dependency: ${dep}`);
    }
  });

  console.log('  - All core dependencies listed');
});

// Test 6: Verify source files exist
test('Source files exist', () => {
  const filesToCheck = [
    '../src/main.tsx',
    '../src/App.tsx',
    '../src/physics.ts',
    '../src/particles.ts',
    '../src/components/MapView.tsx',
    '../src/components/CityCombobox.tsx',
    '../src/components/Controls.tsx',
    '../src/components/InfoCard.tsx',
    '../src/styles/app.css',
    '../src/utils/export.ts'
  ];

  filesToCheck.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${file}`);
    }
  });

  console.log(`  - All ${filesToCheck.length} source files exist`);
});

// Test 7: Verify outputs directory exists
test('Outputs directory exists', () => {
  const outputsPath = path.join(__dirname, '../outputs');
  if (!fs.existsSync(outputsPath)) {
    throw new Error('outputs/ directory not found');
  }

  console.log('  - Outputs directory ready');
});

// Test 8: Verify README exists and has Quick Start
test('README exists with Quick Start section', () => {
  const readmePath = path.join(__dirname, '../README.md');
  if (!fs.existsSync(readmePath)) {
    throw new Error('README.md not found');
  }

  const content = fs.readFileSync(readmePath, 'utf8');

  if (!content.includes('Quick Start')) {
    throw new Error('README missing Quick Start section');
  }

  if (!content.includes('npm run dev')) {
    throw new Error('README missing npm run dev command');
  }

  console.log('  - README complete');
});

// Summary
console.log('\n============================================================');
if (passedTests === totalTests) {
  console.log(`  ✓ ALL TESTS PASSED (${passedTests}/${totalTests})`);
  console.log('============================================================\n');
  console.log('Ready to run: npm install && npm run dev');
  process.exit(0);
} else {
  console.log(`  ✗ SOME TESTS FAILED (${passedTests}/${totalTests} passed)`);
  console.log('============================================================\n');
  process.exit(1);
}
