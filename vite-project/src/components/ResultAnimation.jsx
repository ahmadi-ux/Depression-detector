import { useEffect } from 'react';

/**
 * Result Animation Component
 * Displays celebratory animations based on depression prediction
 * - "not-depressed": Fireworks confetti celebration
 * - "depressed": Falling skulls with pulse effect
 */
export function ResultAnimation({ prediction, onComplete }) {
  useEffect(() => {
    if (!prediction) return;

    if (prediction === 'not-depressed') {
      triggerFireworks();
    } else if (prediction === 'depressed') {
      triggerSkullAnimation();
    }

    // Cleanup function
    return () => {
      // Optional: clean up any remaining elements
    };
  }, [prediction]);

  return null;
}

/**
 * Trigger celebratory fireworks using native canvas animation
 */
function triggerFireworks() {
  // Create multiple bursts
  const numberOfBursts = 4;
  const positions = [
    { x: 0.25, y: 0.6 },
    { x: 0.75, y: 0.6 },
    { x: 0.5, y: 0.3 },
    { x: 0.5, y: 0.8 },
  ];

  positions.forEach((pos, index) => {
    setTimeout(() => {
      createConfetti(pos.x, pos.y);
    }, index * 150);
  });
}

/**
 * Create confetti burst at specified position
 */
function createConfetti(x, y) {
  const canvas = document.createElement('canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 100;
  `;
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  const particles = [];

  // Create particles
  for (let i = 0; i < 50; i++) {
    const angle = (Math.PI * 2 * i) / 50;
    const velocity = 5 + Math.random() * 5;
    particles.push({
      x: x * canvas.width,
      y: y * canvas.height,
      vx: Math.cos(angle) * velocity,
      vy: Math.sin(angle) * velocity - 2,
      life: 1,
      color: `hsl(${Math.random() * 360}, 100%, 50%)`,
      size: 5 + Math.random() * 5,
    });
  }

  let animationId;
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let hasParticles = false;
    particles.forEach((p) => {
      if (p.life > 0) {
        hasParticles = true;
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.2; // gravity
        p.life -= 0.01;

        ctx.globalAlpha = p.life;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    ctx.globalAlpha = 1;

    if (hasParticles) {
      animationId = requestAnimationFrame(animate);
    } else {
      canvas.remove();
      cancelAnimationFrame(animationId);
    }
  };

  animate();
}

/**
 * Trigger crying face falling animation and sound
 */
function triggerSkullAnimation() {
  const skullContainer = document.createElement('div');
  skullContainer.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 100;
  `;

  // Add CSS animation
  const style = document.createElement('style');
  style.innerHTML = `
    @keyframes cryingFall {
      0% {
        transform: translateY(-100px) rotateZ(0deg);
        opacity: 1;
      }
      100% {
        transform: translateY(100vh) rotateZ(720deg);
        opacity: 0;
      }
    }

    @keyframes cryingPulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.1);
      }
    }

    .crying-emoji {
      position: absolute;
      font-size: 3rem;
      animation: cryingFall 3s ease-in forwards;
      opacity: 0.8;
      text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    }

    .crying-emoji:hover {
      animation: cryingPulse 0.3s ease-in-out;
    }
  `;
  document.head.appendChild(style);

  // Create falling crying faces
  const cryingCount = 250;
  for (let i = 0; i < cryingCount; i++) {
    const crying = document.createElement('div');
    crying.className = 'crying-emoji';
    crying.textContent = '😢';

    const startLeft = Math.random() * 100;
    const delay = (i * 80) / cryingCount;

    crying.style.cssText = `
      left: ${startLeft}%;
      top: -50px;
      animation: cryingFall 3s ease-in forwards;
      animation-delay: ${delay}ms;
    `;

    skullContainer.appendChild(crying);
  }

  document.body.appendChild(skullContainer);

  // Clean up after animation
  setTimeout(() => {
    skullContainer.remove();
    style.remove();
  }, 3500);

  // Optional: Play a subtle sound effect (uncomment if you have audio files)
  // playCryingSound();
}

/**
 * Optional: Play sound effect
 */
function playCryingSound() {
  try {
    // You can add sound files to public/ folder and play them here
    const audio = new Audio('/smg4-sound-effects-well-ive-done-all-i-can-do.mp3');
    audio.volume = 0.3;
    audio.play().catch(() => {
      // Silently fail if audio not available
    });
  } catch (e) {
    // Audio support not available
  }
}

export default ResultAnimation;
