const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const bestScoreEl = document.getElementById('best-score');
const overlay = document.getElementById('overlay');
const leftBtn = document.getElementById('leftBtn');
const rightBtn = document.getElementById('rightBtn');

const laneCenters = [-1.25, 0, 1.25];
const road = { horizon: canvas.height * 0.22, bottom: canvas.height };

let gameState = 'ready';
let score = 0;
let bestScore = Number(localStorage.getItem('turbo-drift-best')) || 0;
let lastTime = 0;
let spawnTimer = 0;
let baseSpeed = 220;
let roadScroll = 0;

const enemyCars = [];
const keys = { left: false, right: false };

const player = {
  x: 0,
  y: canvas.height - 120,
  width: 330,
  height: 220,
  velocity: 0,
  tilt: 0,
  maxSpeed: 2.6,
  color: '#f6b400',
};

let audioCtx = null;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function ensureAudio() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) {
      audioCtx = new Ctx();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function playTone(freq, duration = 0.12, type = 'square', volume = 0.04, sweep = 0) {
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  const now = audioCtx.currentTime;

  osc.type = type;
  osc.frequency.setValueAtTime(freq, now);
  if (sweep !== 0) {
    osc.frequency.linearRampToValueAtTime(freq + sweep, now + duration);
  }

  gain.gain.setValueAtTime(0.001, now);
  gain.gain.exponentialRampToValueAtTime(volume, now + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start(now);
  osc.stop(now + duration);
}

function playStartSound() {
  ensureAudio();
  playTone(320, 0.08, 'triangle', 0.05, 180);
  setTimeout(() => playTone(520, 0.12, 'triangle', 0.05, 220), 80);
}

function playCrashSound() {
  ensureAudio();
  playTone(180, 0.2, 'sawtooth', 0.07, -80);
  setTimeout(() => playTone(90, 0.26, 'square', 0.07, -30), 90);
}

function updateHud() {
  scoreEl.textContent = Math.floor(score);
  bestScoreEl.textContent = Math.floor(bestScore);
}

function resetPlayerPosition() {
  player.x = 0;
  player.y = canvas.height - 120;
  player.velocity = 0;
  player.tilt = 0;
}

function setOverlay(text, buttonText) {
  overlay.innerHTML = `
    <h1>Turbo Drift</h1>
    <p>${text}</p>
    <button id="startBtn">${buttonText}</button>
  `;
  const startButton = document.getElementById('startBtn');
  if (startButton) startButton.addEventListener('click', startGame);
}

function showReadyState() {
  gameState = 'ready';
  overlay.classList.remove('hidden');
  overlay.classList.add('visible');
  setOverlay('Use arrow keys or A / D to dodge traffic', 'Start Race');
}

function showGameOver() {
  gameState = 'over';
  if (score > bestScore) {
    bestScore = score;
    localStorage.setItem('turbo-drift-best', String(bestScore));
  }
  updateHud();
  overlay.classList.remove('hidden');
  overlay.classList.add('visible');
  setOverlay(`You scored ${Math.floor(score)} points`, 'Race Again');
}

function startGame() {
  ensureAudio();
  score = 0;
  spawnTimer = 0;
  baseSpeed = 220;
  roadScroll = 0;
  enemyCars.length = 0;
  resetPlayerPosition();
  gameState = 'playing';
  overlay.classList.add('hidden');
  updateHud();
  playStartSound();
}

function spawnEnemy() {
  const lane = Math.floor(Math.random() * laneCenters.length);
  const colorPool = ['#ff6b6b', '#f7b267', '#5ac8fa', '#d4a5ff', '#ffd166'];
  enemyCars.push({
    lane,
    x: laneCenters[lane],
    y: -100,
    width: 120,
    height: 180,
    color: colorPool[Math.floor(Math.random() * colorPool.length)],
    speed: 180 + Math.random() * 120,
  });
}

function update(dt) {
  if (gameState !== 'playing') return;

  score += dt * 18;
  baseSpeed = 220 + score * 7;
  roadScroll += dt * baseSpeed * 0.65;
  spawnTimer += dt;

  if (spawnTimer > Math.max(0.6, 1.25 - score * 0.02)) {
    spawnEnemy();
    spawnTimer = 0;
  }

  const inputDir = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
  if (inputDir !== 0) player.velocity += inputDir * 2.8;

  player.velocity *= 0.82;
  player.velocity = clamp(player.velocity, -player.maxSpeed, player.maxSpeed);
  player.x += player.velocity * dt * 1.7;
  player.x = clamp(player.x, -1.8, 1.8);
  player.tilt = lerp(player.tilt, inputDir * 0.35 + player.velocity * 0.22, 0.12);

  for (const car of enemyCars) {
    car.y += (baseSpeed + car.speed) * dt * 0.6;
  }

  for (let i = enemyCars.length - 1; i >= 0; i--) {
    const enemy = enemyCars[i];
    if (enemy.y > canvas.height + enemy.height) {
      enemyCars.splice(i, 1);
      continue;
    }

    const xGap = Math.abs(player.x - enemy.x);
    const yGap = Math.abs(player.y - enemy.y);
    if (xGap < 0.52 && yGap < 90) {
      gameState = 'over';
      playCrashSound();
      showGameOver();
      return;
    }
  }

  updateHud();
}

function drawSky() {
  const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
  g.addColorStop(0, '#77c9ef');
  g.addColorStop(0.48, '#4d9ad7');
  g.addColorStop(1, '#0a1d35');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < 25; i++) {
    const x = (i * 47 + 18) % canvas.width;
    const y = 30 + ((i * 31) % 140);
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.fillRect(x, y, 4, 4);
  }
}

function drawCity() {
  const buildings = [
    { x: 0, w: 80, h: 180 },
    { x: 110, w: 95, h: 220 },
    { x: 220, w: 90, h: 170 },
    { x: 330, w: 100, h: 240 },
    { x: 450, w: 110, h: 200 },
    { x: 580, w: 80, h: 190 },
    { x: 680, w: 120, h: 260 },
  ];

  ctx.fillStyle = 'rgba(35, 77, 122, 0.9)';
  buildings.forEach((b) => {
    const x = b.x;
    const y = canvas.height * 0.32 - b.h;
    ctx.fillRect(x, y, b.w, b.h);

    ctx.fillStyle = 'rgba(160, 208, 255, 0.38)';
    for (let row = 0; row < 6; row++) {
      for (let col = 0; col < 4; col++) {
        const wx = x + 10 + col * 18;
        const wy = y + 18 + row * 22;
        ctx.fillRect(wx, wy, 10, 10);
      }
    }
    ctx.fillStyle = 'rgba(35, 77, 122, 0.9)';
  });

  ctx.fillStyle = 'rgba(72, 128, 62, 0.9)';
  ctx.fillRect(0, canvas.height * 0.58, canvas.width, 120);
}

function drawRoadPerspective() {
  const horizon = canvas.height * 0.28;
  const bottom = canvas.height;
  const roadWidthTop = 80;
  const roadWidthBottom = canvas.width * 0.95;

  ctx.fillStyle = '#0d1b2f';
  ctx.fillRect(0, horizon, canvas.width, canvas.height - horizon);

  for (let i = 0; i < 26; i++) {
    const t0 = i / 26;
    const t1 = (i + 1) / 26;
    const y0 = horizon + Math.pow(t0, 1.8) * (bottom - horizon);
    const y1 = horizon + Math.pow(t1, 1.8) * (bottom - horizon);
    const half0 = lerp(roadWidthTop / 2, roadWidthBottom / 2, t0);
    const half1 = lerp(roadWidthTop / 2, roadWidthBottom / 2, t1);

    ctx.fillStyle = i % 2 === 0 ? '#2d3135' : '#353b42';
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2 - half0, y0);
    ctx.lineTo(canvas.width / 2 + half0, y0);
    ctx.lineTo(canvas.width / 2 + half1, y1);
    ctx.lineTo(canvas.width / 2 - half1, y1);
    ctx.closePath();
    ctx.fill();
  }

  ctx.strokeStyle = '#dfe7f2';
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2 - roadWidthBottom / 2, bottom);
  ctx.lineTo(canvas.width / 2 - roadWidthTop / 2, horizon);
  ctx.moveTo(canvas.width / 2 + roadWidthBottom / 2, bottom);
  ctx.lineTo(canvas.width / 2 + roadWidthTop / 2, horizon);
  ctx.stroke();

  ctx.strokeStyle = 'rgba(255,255,255,0.9)';
  ctx.lineWidth = 4;
  ctx.setLineDash([18, 18]);
  for (let i = 1; i < 3; i++) {
    const laneRatio = i / 3;
    ctx.beginPath();
    for (let step = 0; step <= 30; step++) {
      const t = step / 30;
      const y = horizon + Math.pow(t, 1.8) * (bottom - horizon);
      const half = lerp(roadWidthTop / 2, roadWidthBottom / 2, t);
      const x = canvas.width / 2 + (laneRatio * 2 - 1) * half;
      if (step === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  ctx.setLineDash([]);

  ctx.fillStyle = '#d5e0ef';
  for (let i = 0; i < 18; i++) {
    const t = (i / 18 + roadScroll * 0.0009) % 1;
    const y = horizon + Math.pow(t, 1.8) * (bottom - horizon);
    const half = lerp(roadWidthTop / 2, roadWidthBottom / 2, t);
    ctx.fillRect(canvas.width / 2 - half + 12, y, 7, 16);
    ctx.fillRect(canvas.width / 2 + half - 19, y, 7, 16);
  }
}

function drawCarSprite(x, y, width, height, color, isPlayer = false) {
  const screenX = canvas.width / 2 + x * 270;
  const carW = width;
  const carH = height;

  ctx.save();
  ctx.translate(screenX, y);
  ctx.rotate(isPlayer ? player.tilt : 0);

  ctx.fillStyle = 'rgba(0, 0, 0, 0.22)';
  ctx.fillRect(-carW * 0.72, carH * 0.4, carW * 1.44, 14);

  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(-carW * 0.38, -carH * 0.48);
  ctx.lineTo(carW * 0.38, -carH * 0.48);
  ctx.quadraticCurveTo(carW * 0.46, -carH * 0.48, carW * 0.5, -carH * 0.2);
  ctx.lineTo(carW * 0.45, carH * 0.42);
  ctx.quadraticCurveTo(carW * 0.32, carH * 0.52, 0, carH * 0.54);
  ctx.quadraticCurveTo(-carW * 0.32, carH * 0.52, -carW * 0.45, carH * 0.42);
  ctx.lineTo(-carW * 0.5, -carH * 0.2);
  ctx.quadraticCurveTo(-carW * 0.46, -carH * 0.48, -carW * 0.38, -carH * 0.48);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#104065';
  ctx.beginPath();
  ctx.moveTo(-carW * 0.24, -carH * 0.18);
  ctx.lineTo(carW * 0.24, -carH * 0.18);
  ctx.quadraticCurveTo(carW * 0.28, -carH * 0.02, 0, carH * 0.04);
  ctx.quadraticCurveTo(-carW * 0.28, -carH * 0.02, -carW * 0.24, -carH * 0.18);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#d6ecff';
  ctx.fillRect(-carW * 0.16, -carH * 0.12, carW * 0.32, carH * 0.1);

  ctx.fillStyle = '#111827';
  ctx.fillRect(-carW * 0.38, -carH * 0.38, 18, 28);
  ctx.fillRect(carW * 0.38 - 18, -carH * 0.38, 18, 28);
  ctx.fillRect(-carW * 0.38, carH * 0.14, 18, 28);
  ctx.fillRect(carW * 0.38 - 18, carH * 0.14, 18, 28);

  ctx.fillStyle = '#ff2f2f';
  ctx.fillRect(-carW * 0.18, carH * 0.42, 22, 12);
  ctx.fillRect(carW * 0.18 - 22, carH * 0.42, 22, 12);

  ctx.fillStyle = '#1d1d1d';
  ctx.fillRect(-carW * 0.42, -carH * 0.12, 10, 28);
  ctx.fillRect(carW * 0.42 - 10, -carH * 0.12, 10, 28);

  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  ctx.fillRect(-carW * 0.22, -carH * 0.3, carW * 0.16, carH * 0.12);
  ctx.fillRect(carW * 0.06, -carH * 0.3, carW * 0.16, carH * 0.12);

  ctx.restore();
}

function drawCars() {
  drawCarSprite(player.x, player.y, player.width, player.height, player.color, true);
  for (const car of enemyCars) {
    drawCarSprite(car.x, car.y, car.width, car.height, car.color, false);
  }
}

function draw() {
  drawSky();
  drawCity();
  drawRoadPerspective();
  drawCars();
}

function loop(timestamp) {
  const dt = (timestamp - lastTime) / 1000 || 0.016;
  lastTime = timestamp;

  update(dt);
  draw();
  requestAnimationFrame(loop);
}

window.addEventListener('keydown', (event) => {
  const key = event.key.toLowerCase();
  if (key === 'arrowleft' || key === 'a') keys.left = true;
  if (key === 'arrowright' || key === 'd') keys.right = true;
  if (event.key === ' ' && gameState !== 'playing') startGame();
});

window.addEventListener('keyup', (event) => {
  const key = event.key.toLowerCase();
  if (key === 'arrowleft' || key === 'a') keys.left = false;
  if (key === 'arrowright' || key === 'd') keys.right = false;
});

leftBtn.addEventListener('pointerdown', () => { keys.left = true; ensureAudio(); });
leftBtn.addEventListener('pointerup', () => keys.left = false);
leftBtn.addEventListener('pointerleave', () => keys.left = false);

rightBtn.addEventListener('pointerdown', () => { keys.right = true; ensureAudio(); });
rightBtn.addEventListener('pointerup', () => keys.right = false);
rightBtn.addEventListener('pointerleave', () => keys.right = false);

window.addEventListener('pointerdown', ensureAudio, { once: true });

updateHud();
startGame();
requestAnimationFrame(loop);
