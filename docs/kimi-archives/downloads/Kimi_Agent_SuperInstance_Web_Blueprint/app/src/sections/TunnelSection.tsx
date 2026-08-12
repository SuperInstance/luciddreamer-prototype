import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export function TunnelSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const tunnelRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const tunnel = tunnelRef.current;
    const text = textRef.current;

    if (!section || !tunnel || !text) return;

    const ctx = gsap.context(() => {
      const rings = tunnel.querySelectorAll('.tunnel-ring');

      const scrollTl = gsap.timeline({
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: '+=130%',
          pin: true,
          scrub: 0.7,
        },
      });

      // ENTRANCE (0-30%): Rings scale in
      scrollTl
        .fromTo(
          rings,
          { scale: 0.25, opacity: 0, rotation: -8 },
          {
            scale: 1,
            opacity: 1,
            rotation: 0,
            stagger: 0.05,
            ease: 'power2.out',
          },
          0
        )
        .fromTo(text, { opacity: 0, y: 14 }, { opacity: 1, y: 0, ease: 'power2.out' }, 0.1);

      // SETTLE (30-70%): Subtle rotation
      scrollTl.to(rings, { rotation: 6, duration: 0.4, ease: 'none' }, 0.3);

      // EXIT (70-100%): Expand and fade
      scrollTl
        .to(rings, {
          scale: 2.2,
          opacity: 0,
          stagger: 0.03,
          ease: 'power2.in',
        }, 0.7)
        .to(text, { opacity: 0, ease: 'power2.in' }, 0.72);
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative w-full h-screen flex items-center justify-center overflow-hidden bg-space"
      style={{ zIndex: 30 }}
    >
      {/* Tunnel Rings */}
      <div ref={tunnelRef} className="absolute inset-0 flex items-center justify-center">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="tunnel-ring absolute rounded-full border border-lime/20"
            style={{
              width: `${(i + 1) * 15}%`,
              height: `${(i + 1) * 15}%`,
              opacity: 0.3 - i * 0.04,
            }}
          >
            {/* Radial lines */}
            <svg
              className="absolute inset-0 w-full h-full"
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
            >
              {[...Array(12)].map((_, j) => (
                <line
                  key={j}
                  x1="50"
                  y1="50"
                  x2={50 + 45 * Math.cos((j * Math.PI) / 6)}
                  y2={50 + 45 * Math.sin((j * Math.PI) / 6)}
                  stroke="rgba(200, 255, 46, 0.1)"
                  strokeWidth="0.2"
                />
              ))}
            </svg>
          </div>
        ))}

        {/* Center glow */}
        <div className="absolute w-32 h-32 rounded-full bg-lime/10 blur-3xl" />
      </div>

      {/* Center Text */}
      <p
        ref={textRef}
        className="relative z-10 font-mono text-sm tracking-[0.3em] text-lime/80 uppercase"
      >
        Enter the swarm
      </p>
    </section>
  );
}
