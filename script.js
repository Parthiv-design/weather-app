// 1. Live Running Clock
function updateClock() {
    const clockElement = document.getElementById('live-clock');
    if (clockElement) {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    }
}

// 2. CSP-Compliant Unit Switcher
function initUnitToggle() {
    const toggleBtn = document.getElementById('unit-toggle-btn');
    const toggleDot = document.getElementById('toggle-dot');
    if (!toggleBtn) return;
    let isCelsius = true;

    toggleBtn.addEventListener('click', () => {
        isCelsius = !isCelsius;
        const allTemps = document.querySelectorAll('[data-celsius]');
        allTemps.forEach(element => {
            element.textContent = isCelsius ? element.getAttribute('data-celsius') : element.getAttribute('data-fahrenheit');
        });
        toggleDot.style.transform = isCelsius ? 'translateX(0px)' : 'translateX(20px)';
        toggleBtn.style.backgroundColor = isCelsius ? '' : '#22d3ee';
    });
}

// 3. Immersive HTML5 Background Environment Engine
function initWeatherAnimation() {
    const canvas = document.getElementById('weather-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const condition = document.body.getAttribute('data-condition') || 'clear';

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const particles = [];
    let maxParticles = 80;
    
    if (condition === 'thunderstorm') maxParticles = 140;
    if (condition === 'drizzle') maxParticles = 150;
    if (condition === 'fog') maxParticles = 40;

    for (let i = 0; i < maxParticles; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            velX: condition === 'snow' || condition === 'fog' ? (Math.random() * 0.6 - 0.3) : 0,
            velY: condition === 'snow' ? (Math.random() * 0.8 + 0.8) : 
                  condition === 'drizzle' ? (Math.random() * 4 + 4) :
                  condition === 'rain' || condition === 'thunderstorm' ? Math.random() * 15 + 15 : 0,
            length: condition === 'rain' || condition === 'thunderstorm' ? Math.random() * 20 + 15 :
                    condition === 'drizzle' ? Math.random() * 6 + 6 : 
                    condition === 'fog' ? Math.random() * 60 + 40 : Math.random() * 3 + 2,
            opacity: Math.random() * 0.4 + 0.1
        });
    }

    if (condition === 'thunderstorm') {
        const flashDiv = document.getElementById('lightning-flash');
        function triggerLightning() {
            if (flashDiv) {
                flashDiv.classList.add('strike-active');
                setTimeout(() => flashDiv.classList.remove('strike-active'), 500);
            }
            setTimeout(triggerLightning, Math.random() * 7000 + 4000);
        }
        setTimeout(triggerLightning, 3000);
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (condition === 'clear') {
            ctx.fillStyle = 'rgba(255, 253, 230, 0.03)';
            ctx.beginPath();
            ctx.arc(canvas.width * 0.8, canvas.height * 0.2, 200, 0, Math.PI * 2);
            ctx.fill();
            return requestAnimationFrame(animate);
        }

        particles.forEach(p => {
            ctx.beginPath();
            if (condition === 'snow') {
                ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
                ctx.arc(p.x, p.y, p.length, 0, Math.PI * 2);
                ctx.fill();
            } else if (condition === 'fog') {
                // Renders large, smooth mist clouds for fog effects
                ctx.fillStyle = `rgba(220, 225, 235, ${p.opacity * 0.2})`;
                ctx.arc(p.x, p.y, p.length, 0, Math.PI * 2);
                ctx.fill();
            } else if (condition === 'rain' || condition === 'thunderstorm' || condition === 'drizzle') {
                ctx.strokeStyle = `rgba(174, 219, 255, ${p.opacity})`;
                ctx.lineWidth = condition === 'drizzle' ? 1 : 2;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p.x, p.y + p.length);
                ctx.stroke();
            }

            p.x += p.velX;
            p.y += p.velY;

            if (p.y > canvas.height + 20 || p.x > canvas.width + 20 || p.x < -20) {
                p.y = -20;
                p.x = Math.random() * canvas.width;
            }
        });

        requestAnimationFrame(animate);
    }
    animate();
}

document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    initUnitToggle();
    initWeatherAnimation();
});
