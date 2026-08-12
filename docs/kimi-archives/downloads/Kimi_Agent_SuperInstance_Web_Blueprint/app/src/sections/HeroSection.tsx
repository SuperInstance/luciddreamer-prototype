import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ChevronDown } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

export function HeroSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const taglineRef = useRef<HTMLParagraphElement>(null);
  const versionRef = useRef<HTMLSpanElement>(null);
  const scrollHintRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const logo = logoRef.current;
    const tagline = taglineRef.current;
    const version = versionRef.current;
    const scrollHint = scrollHintRef.current;

    if (!section || !logo || !tagline || !version || !scrollHint) return;

    const ctx = gsap.context(() => {
      // Auto-play entrance animation
      const tl = gsap.timeline({ delay: 0.3 });

      tl.fromTo(
        logo.querySelector('.logo-mark'),
        { scale: 0.85, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.6, ease: 'power2.out' }
      )
        .fromTo(
          logo.querySelector('.logo-text'),
          { y: 18, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' },
          '-=0.3'
        )
        .fromTo(
          tagline,
          { opacity: 0 },
          { opacity: 1, duration: 0.6, ease: 'power2.out' },
          '-=0.2'
        )
        .fromTo(
          version,
          { opacity: 0 },
          { opacity: 1, duration: 0.4 },
          '-=0.3'
        )
        .fromTo(
          scrollHint,
          { opacity: 0, y: 10 },
          { opacity: 1, y: 0, duration: 0.4 },
          '-=0.2'
        );

      // Scroll-driven exit animation
      const scrollTl = gsap.timeline({
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: '+=130%',
          pin: true,
          scrub: 0.6,
          onLeaveBack: () => {
            // Reset to visible when scrolling back to top
            gsap.set([logo, tagline, version, scrollHint], {
              opacity: 1,
              y: 0,
              scale: 1,
            });
          },
        },
      });

      // ENTRANCE (0-30%): Hold position (already visible from load animation)
      // SETTLE (30-70%): Hold
      // EXIT (70-100%): Fade out and scale up
      scrollTl
        .fromTo(
          logo,
          { opacity: 1, scale: 1 },
          { opacity: 0, scale: 1.06, ease: 'power2.in' },
          0.7
        )
        .fromTo(
          tagline,
          { opacity: 1, y: 0 },
          { opacity: 0, y: -20, ease: 'power2.in' },
          0.72
        )
        .fromTo(
          version,
          { opacity: 1 },
          { opacity: 0, ease: 'power2.in' },
          0.75
        )
        .fromTo(
          scrollHint,
          { opacity: 1 },
          { opacity: 0, ease: 'power2.in' },
          0.7
        );
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative w-full h-screen flex items-center justify-center overflow-hidden"
      style={{ zIndex: 10 }}
    >
      {/* Vignette overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center, transparent 0%, rgba(7, 4, 10, 0.4) 100%)',
        }}
      />

      {/* Center Logo Lockup */}
      <div
        ref={logoRef}
        className="relative z-10 flex flex-col items-center text-center px-6"
        style={{ transform: 'translateY(-5%)' }}
      >
        {/* Logo Mark */}
        <div className="logo-mark mb-6 relative">
          <svg
            width="72"
            height="72"
            viewBox="0 0 72 72"
            fill="none"
            className="animate-pulse-glow"
          >
            <defs>
              <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#C8FF2E" />
                <stop offset="100%" stopColor="#9AE600" />
              </linearGradient>
            </defs>
            <path
              d="M36 4L64 20V52L36 68L8 52V20L36 4Z"
              stroke="url(#logoGrad)"
              strokeWidth="2"
              fill="none"
            />
            <path
              d="M36 16L52 26V46L36 56L20 46V26L36 16Z"
              stroke="url(#logoGrad)"
              strokeWidth="1.5"
              fill="none"
              opacity="0.6"
            />
            <circle cx="36" cy="36" r="4" fill="url(#logoGrad)" />
          </svg>
          {/* Glow effect */}
          <div className="absolute inset-0 blur-2xl bg-lime/20 rounded-full scale-150 -z-10" />
        </div>

        {/* Brand Wordmark */}
        <h1 className="logo-text font-display font-bold text-4xl sm:text-5xl md:text-6xl lg:text-7xl text-foreground tracking-tight mb-4">
          SuperInstance
        </h1>

        {/* Tagline */}
        <p
          ref={taglineRef}
          className="font-mono text-xs sm:text-sm tracking-[0.2em] text-muted-foreground uppercase"
        >
          The Architecture for Embodied Intelligence
        </p>
      </div>

      {/* Bottom Left: Version */}
      <span
        ref={versionRef}
        className="absolute bottom-8 left-6 lg:left-12 font-mono text-xs text-muted-foreground"
      >
        v0.9.2
      </span>

      {/* Bottom Right: Scroll Hint */}
      <div
        ref={scrollHintRef}
        className="absolute bottom-8 right-6 lg:right-12 flex items-center gap-2 text-muted-foreground"
      >
        <span className="font-mono text-xs">Scroll to enter</span>
        <ChevronDown className="w-4 h-4 animate-bounce" />
      </div>
    </section>
  );
}
