import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { ArrowRight, Github } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

export function ManifestoSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const bodyRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const headline = headlineRef.current;
    const body = bodyRef.current;
    const cta = ctaRef.current;

    if (!section || !headline || !body || !cta) return;

    const ctx = gsap.context(() => {
      // Split headline into words
      const words = headline.innerText.split(' ');
      headline.innerHTML = words
        .map((word) => `<span class="inline-block overflow-hidden"><span class="word inline-block">${word}</span></span>`)
        .join(' ');

      const wordSpans = headline.querySelectorAll('.word');

      const scrollTl = gsap.timeline({
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: '+=130%',
          pin: true,
          scrub: 0.6,
        },
      });

      // ENTRANCE (0-30%)
      scrollTl
        .fromTo(
          wordSpans,
          { opacity: 0, y: 40, scale: 0.985 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            stagger: 0.03,
            ease: 'power2.out',
          },
          0
        )
        .fromTo(
          body,
          { opacity: 0, y: 22 },
          { opacity: 1, y: 0, ease: 'power2.out' },
          0.1
        )
        .fromTo(
          cta,
          { opacity: 0, y: 18, scale: 0.98 },
          { opacity: 1, y: 0, scale: 1, ease: 'power2.out' },
          0.15
        );

      // SETTLE (30-70%): Hold - elements stay visible

      // EXIT (70-100%)
      scrollTl
        .to(wordSpans, {
          opacity: 0,
          y: -28,
          stagger: 0.02,
          ease: 'power2.in',
        }, 0.7)
        .to(body, { opacity: 0, y: -16, ease: 'power2.in' }, 0.72)
        .to(cta, { opacity: 0, y: -12, ease: 'power2.in' }, 0.74);
    }, section);

    return () => ctx.revert();
  }, []);

  const scrollToCapabilities = () => {
    const element = document.querySelector('#capabilities');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToCommunity = () => {
    const element = document.querySelector('#community');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section
      ref={sectionRef}
      className="relative w-full h-screen flex items-center justify-center overflow-hidden bg-space"
      style={{ zIndex: 20 }}
    >
      {/* Faint network remnants */}
      <div className="absolute inset-0 opacity-30">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 20% 30%, rgba(200, 255, 46, 0.03) 0%, transparent 50%),
                              radial-gradient(circle at 80% 70%, rgba(200, 255, 46, 0.02) 0%, transparent 40%)`,
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-4xl mx-auto px-6 text-center">
        <h2
          ref={headlineRef}
          className="font-display font-bold text-2xl sm:text-3xl md:text-4xl lg:text-5xl text-foreground leading-tight mb-8"
        >
          We're building the underlying intelligence for the next generation of computing.
        </h2>

        <p
          ref={bodyRef}
          className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          Not another chatbot. A co-processor that lives on your devices, learns from you
          continuously, and becomes an extension of your will. Fast, private, and improving
          every single day.
        </p>

        <div ref={ctaRef} className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            size="lg"
            className="bg-lime text-space hover:bg-lime-dark font-semibold rounded-full px-8 group"
            onClick={scrollToCapabilities}
          >
            Explore the Architecture
            <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-white/20 text-foreground hover:bg-white/5 rounded-full px-8"
            onClick={scrollToCommunity}
          >
            <Github className="w-4 h-4 mr-2" />
            Join the Build
          </Button>
        </div>
      </div>
    </section>
  );
}
