import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { Zap, Server, Globe, ArrowRight } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const features = [
  { icon: Server, label: 'Spot-instance orchestration' },
  { icon: Zap, label: 'One-click training' },
  { icon: Globe, label: 'Edge-to-cloud continuum' },
];

export function CloudSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const chipsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const image = imageRef.current;
    const text = textRef.current;
    const chips = chipsRef.current;

    if (!section || !image || !text || !chips) return;

    const ctx = gsap.context(() => {
      // Image animation
      gsap.fromTo(
        image,
        { opacity: 0, y: 50, scale: 0.985 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: image,
            start: 'top 80%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Image parallax
      const img = image.querySelector('img');
      if (img) {
        gsap.fromTo(
          img,
          { y: -10 },
          {
            y: 10,
            ease: 'none',
            scrollTrigger: {
              trigger: image,
              start: 'top bottom',
              end: 'bottom top',
              scrub: true,
            },
          }
        );
      }

      // Text animation
      gsap.fromTo(
        text,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.6,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: text,
            start: 'top 85%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Chips animation
      const chipItems = chips.querySelectorAll('.feature-chip');
      gsap.fromTo(
        chipItems,
        { opacity: 0, y: 18, scale: 0.98 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.4,
          stagger: 0.1,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: chips,
            start: 'top 90%',
            toggleActions: 'play none none reverse',
          },
        }
      );
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="cloud"
      className="relative w-full py-24 lg:py-32 bg-space-light"
      style={{ zIndex: 60 }}
    >
      <div className="relative z-10 w-full px-6 lg:px-12">
        <div className="max-w-5xl mx-auto">
          {/* Top Image */}
          <div
            ref={imageRef}
            className="relative rounded-2xl overflow-hidden border border-white/5 h-64 sm:h-80 lg:h-96 mb-12"
          >
            <img
              src="/cloud_photo.jpg"
              alt="LucidDreamer Cloud"
              className="absolute inset-0 w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-space-light via-space-light/50 to-transparent" />
          </div>

          {/* Text Content */}
          <div ref={textRef} className="text-center mb-10">
            <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-foreground mb-6">
              LucidDreamer<span className="text-lime">.ai</span>
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              The invisible backbone for the Mycelium ecosystem. Train on spot instances across
              providers—Vast, AWS, and more—without managing infrastructure.
            </p>
          </div>

          {/* Feature Chips */}
          <div
            ref={chipsRef}
            className="flex flex-wrap justify-center gap-3 mb-10"
          >
            {features.map((feature) => (
              <div
                key={feature.label}
                className="feature-chip flex items-center gap-2 px-4 py-2 rounded-full bg-space border border-white/10"
              >
                <feature.icon className="w-4 h-4 text-lime" />
                <span className="text-sm text-foreground">{feature.label}</span>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="text-center">
            <Button
              size="lg"
              className="bg-lime text-space hover:bg-lime-dark font-semibold rounded-full px-8 group"
              onClick={() => window.open('https://luciddreamer.ai', '_blank')}
            >
              Request Early Access
              <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
