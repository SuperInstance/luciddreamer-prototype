import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { Github, Star, Users, FileText } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const stats = [
  { icon: Star, value: '12k+', label: 'Stars' },
  { icon: Users, value: '180+', label: 'Contributors' },
  { icon: FileText, value: 'Apache 2.0', label: 'License' },
];

export function CommunitySection() {
  const sectionRef = useRef<HTMLElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const text = textRef.current;
    const image = imageRef.current;
    const statsEl = statsRef.current;

    if (!section || !text || !image || !statsEl) return;

    const ctx = gsap.context(() => {
      // Text block animation
      gsap.fromTo(
        text,
        { opacity: 0, x: -60 },
        {
          opacity: 1,
          x: 0,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: text,
            start: 'top 80%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Image animation
      gsap.fromTo(
        image,
        { opacity: 0, x: 60, scale: 0.98 },
        {
          opacity: 1,
          x: 0,
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
          { y: -12 },
          {
            y: 12,
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

      // Stats animation
      const statItems = statsEl.querySelectorAll('.stat-item');
      gsap.fromTo(
        statItems,
        { opacity: 0, y: 24 },
        {
          opacity: 1,
          y: 0,
          duration: 0.5,
          stagger: 0.12,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: statsEl,
            start: 'top 85%',
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
      id="community"
      className="relative w-full py-24 lg:py-32 bg-space"
      style={{ zIndex: 50 }}
    >
      <div className="relative z-10 w-full px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left: Text */}
            <div ref={textRef}>
              <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-foreground mb-6">
                Built in the <span className="text-lime">open</span>.
              </h2>
              <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
                Mycelium is open-source because the future of intelligence should be a shared
                endeavor. Read the code, run it locally, and shape the roadmap.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  className="bg-lime text-space hover:bg-lime-dark font-semibold rounded-full px-8"
                  onClick={() => window.open('https://github.com', '_blank')}
                >
                  <Github className="w-5 h-5 mr-2" />
                  Star on GitHub
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="border-white/20 text-foreground hover:bg-white/5 rounded-full px-8"
                  onClick={() => window.open('#', '_blank')}
                >
                  <FileText className="w-5 h-5 mr-2" />
                  Read the Whitepaper
                </Button>
              </div>
            </div>

            {/* Right: Image */}
            <div
              ref={imageRef}
              className="relative rounded-2xl overflow-hidden border border-white/5 h-80 lg:h-[400px]"
            >
              <img
                src="/community_photo.jpg"
                alt="Community"
                className="absolute inset-0 w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-space/80 via-transparent to-transparent" />
            </div>
          </div>

          {/* Stats */}
          <div
            ref={statsRef}
            className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto"
          >
            {stats.map((stat) => (
              <div key={stat.label} className="stat-item text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <stat.icon className="w-5 h-5 text-lime" />
                  <span className="font-display font-bold text-2xl sm:text-3xl text-foreground">
                    {stat.value}
                  </span>
                </div>
                <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
