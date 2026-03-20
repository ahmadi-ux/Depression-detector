import { useEffect, useState, useRef } from 'react';

/**
 * Custom success modal with animations
 * Replaces browser alert() with a styled modal that includes animations
 */
export function SuccessModal({ show, message, classification, onClose }) {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef(null);
  const animationIntervalRef = useRef(null);

  console.log("SuccessModal rendered - show prop:", show, "isVisible state:", isVisible, "classification:", classification);

  useEffect(() => {
    console.log("SuccessModal useEffect - show changed to:", show);
    
    if (show) {
      setIsVisible(true);
      console.log("SuccessModal: Modal should go VISIBLE with classification:", classification);
      
      // Trigger animations immediately and loop them
      if (classification === 'depressed') {
        console.log("SuccessModal: Triggering looping crying animation");
        loopCryingAnimation();
      } else if (classification === 'not-depressed') {
        console.log("SuccessModal: Triggering looping fireworks");
        loopFireworksAnimation();
      }
      
      // Auto-close after 30 seconds (plenty of time to see the animation)
      const timer = setTimeout(() => {
        console.log("SuccessModal: Auto-closing after 30 seconds");
        handleClose();
      }, 30000);
      return () => {
        console.log("SuccessModal: Cleaning up timer and animations");
        clearTimeout(timer);
        if (animationIntervalRef.current) {
          clearInterval(animationIntervalRef.current);
          animationIntervalRef.current = null;
        }
      };
    } else {
      setIsVisible(false);
      if (animationIntervalRef.current) {
        clearInterval(animationIntervalRef.current);
        animationIntervalRef.current = null;
      }
    }
  }, [show, classification]);

  const loopFireworksAnimation = () => {
    // Trigger immediately
    createFireworks();
    playSuccessSound();
    // Then loop every 4 seconds (animation is 3 seconds, +1 second buffer)
    animationIntervalRef.current = setInterval(() => {
      createFireworks();
      playSuccessSound();
    }, 4000);
  };

  const loopCryingAnimation = () => {
    // Trigger immediately
    createCrying();
    playWarningSound();
    // Then loop every 4 seconds (animation is 3 seconds, +1 second buffer)
    animationIntervalRef.current = setInterval(() => {
      createCrying();
      playWarningSound();
    }, 4000);
  };

  const handleClose = () => {
    console.log("SuccessModal: handleClose called");
    setIsVisible(false);
    if (animationIntervalRef.current) {
      clearInterval(animationIntervalRef.current);
      animationIntervalRef.current = null;
    }
    if (onClose) {
      console.log("SuccessModal: Calling onClose callback");
      onClose();
    }
  };

  console.log("SuccessModal: About to check if should return null - isVisible:", isVisible);
  if (!isVisible) {
    console.log("SuccessModal: isVisible is false, returning null (nothing rendered)");
    return null;
  }

  console.log("SuccessModal: Rendering modal UI!");

  return (
    <>
      {/* Overlay - only click overlay to close, not modal */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={handleClose}
        style={{ display: 'block' }}
      />

      {/* Modal Container */}
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}
      >
        {/* Modal Content - prevent clicks from going to overlay */}
        <div 
          className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-11/12 relative"
          style={{ position: 'relative', zIndex: 60, pointerEvents: 'auto' }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Content */}
          <div className="text-center">
            {/* Icon */}
            <div className="mb-4 text-6xl" style={{ marginBottom: '1rem' }}>
              {classification === 'depressed' ? '⚠️' : '✨'}
            </div>

            {/* Message */}
            <h2 className="text-2xl font-bold mb-2" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
              {classification === 'depressed' ? 'Analysis Complete' : 'Great News!'}
            </h2>
            
            <p className="text-gray-600 mb-6" style={{ color: '#666', marginBottom: '1.5rem' }}>
              {message}
            </p>

            {/* Classification Badge */}
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1rem',
              borderRadius: '999px',
              marginBottom: '1.5rem',
              color: 'white',
              fontWeight: 'bold',
              backgroundColor: classification === 'depressed' ? '#eab308' : '#22c55e'
            }}>
              {classification === 'depressed' ? '⚠️ Signs of Depression Detected' : '✨ Low Depression Indicators'}
            </div>

            {/* Close Button */}
            <button
              onClick={handleClose}
              style={{
                marginTop: '1rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                fontWeight: 'bold',
                padding: '0.5rem 1.5rem',
                borderRadius: '0.375rem',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
            >
              Close
            </button>

            {/* Auto-close notice */}
            <p style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.75rem' }}>
              (Closes automatically in 30 seconds)
            </p>
          </div>
        </div>

        {/* Animations (behind modal) */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 45 }} />
      </div>
    </>
  );
}

function createFireworks() {
  // Create confetti on the page
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

function createConfetti(x, y) {
  const canvas = document.createElement('canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 45;
  `;
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  const particles = [];

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
        p.vy += 0.2;
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

function createCrying() {
  const cryingContainer = document.createElement('div');
  cryingContainer.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 45;
  `;

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

    .crying-emoji {
      position: absolute;
      font-size: 3rem;
      animation: cryingFall 3s ease-in forwards;
      opacity: 0.8;
      text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    }
  `;
  document.head.appendChild(style);

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

    cryingContainer.appendChild(crying);
  }

  document.body.appendChild(cryingContainer);

  setTimeout(() => {
    cryingContainer.remove();
    style.remove();
  }, 3500);
}

function playSuccessSound() {
  try {
    const audio = new Audio('/smg4-sound-effects-well-ive-done-all-i-can-do.mp3'); // Audio file in public folder
    audio.volume = 0.5;
    audio.play().catch(() => {
      console.log('Audio playback failed or user denied permission');
    });
  } catch (e) {
    console.log('Audio not available');
  }
}

function playWarningSound() {
  try {
    // Using the same success sound as warning sound since warning-sound.mp3 doesn't exist
    const audio = new Audio('/smg4-sound-effects-well-ive-done-all-i-can-do.mp3'); // Audio file in public folder
    audio.volume = 0.5;
    audio.play().catch(() => {
      console.log('Audio playback failed or user denied permission');
    });
  } catch (e) {
    console.log('Audio not available');
  }
}

export default SuccessModal;
