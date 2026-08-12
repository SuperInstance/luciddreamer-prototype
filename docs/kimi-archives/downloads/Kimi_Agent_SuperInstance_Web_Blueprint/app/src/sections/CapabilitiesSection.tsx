import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Network, GitBranch, Brain, Moon, Eye, Cloud } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const capabilities = [
  {
    icon: Network,
    title: 'Swarm Inference',
    description:
      'Hundreds of tiny specialists run in parallel. Fast, efficient, resilient.',
    image: '/capability_swarm.jpg',
  },
  {
    icon: GitBranch,
    title: 'Plinko Decisions',
    description:
      'A stochastic gating layer that explores safely—more like a brain than a script.',
    image: '/capability_plinko.jpg',
  },
  {
    icon: Brain,
    title: 'Muscle Memory',
    description:
      'Frequent sequences compress into reusable skills. Complex routines become automatic.',
    image: '/capability_memory.jpg',
  },
  {
    icon: Moon,
    title: 'Dreaming',
    description:
      'A learned world model simulates overnight, refining skills without touching your data.',
    image: '/capability_dreaming.jpg',
  },
  {
    icon: Eye,
    title: 'Translator UI',
    description:
      "See the swarm's intent in real time and guide it with simple feedback.",
    image: '/capability_ui.jpg',
  },
  {
    icon: Cloud,
    title: 'Cloud Training',
    description:
      'When you need GPUs, Mycelium connects to the cloud—then returns the model to the edge.',
    image: '/capability_cloud.jpg',
  },
];

export function CapabilitiesSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const section = sectionRef.current;
    const header = headerRef.current;
    const cards = cardsRef.current.filter(Boolean);

    if (!section || !header || cards.length === 0) return;

    const ctx = gsap.context(() => {
      // Header animation
      gsap.fromTo(
        header,
        { opacity: 0, y: 28 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: header,
            start: 'top 80%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Cards animation
      cards.forEach((card, i) => {
        gsap.fromTo(
          card,
          { opacity: 0, y: 40, scale: 0.98 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.6,
            delay: i * 0.08,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: card,
              start: 'top 85%',
              toggleActions: 'play none none reverse',
            },
          }
        );

        // Image parallax
        const img = card?.querySelector('.card-image');
        if (img) {
          gsap.fromTo(
            img,
            { y: -10 },
            {
              y: 10,
              ease: 'none',
              scrollTrigger: {
                trigger: card,
                start: 'top bottom',
                end: 'bottom top',
                scrub: true,
              },
            }
          );
        }
      });
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="capabilities"
      className="relative w-full py-24 lg:py-32 bg-space-light"
      style={{ zIndex: 40 }}
    >
      {/* Faint network overlay */}
      <div className="absolute inset-0 opacity-5">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 50% 50%, rgba(200, 255, 46, 0.1) 0%, transparent 70%)`,
          }}
        />
      </div>

      <div className="relative z-10 w-full px-6 lg:px-12">
        {/* Header */}
        <div ref={headerRef} className="max-w-4xl mb-16">
          <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-foreground mb-6">
            Mycelium runs on your device—
            <span className="text-lime">then scales to the cloud</span> when you need it.
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl">
            A swarm of small models. A probabilistic decision layer. Continuous learning
            while you sleep. And a UI that shows what your AI is thinking.
          </p>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl">
          {capabilities.map((cap, i) => (
            <div
              key={cap.title}
              ref={(el) => { cardsRef.current[i] = el; }}
              className="group relative bg-space rounded-2xl overflow-hidden border border-white/5 hover:border-lime/30 transition-all duration-500 hover:shadow-card"
            >
              {/* Image */}
              <div className="relative h-48 overflow-hidden">
                <img
                  src={cap.image}
                  alt={cap.title}
                  className="card-image absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-space via-space/50 to-transparent" />
              </div>

              {/* Content */}
              <div className="relative p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-lime/10 flex items-center justify-center">
                    <cap.icon className="w-5 h-5 text-lime" />
                  </div>
                  <h3 className="font-display font-semibold text-lg text-foreground">
                    {cap.title}
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {cap.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Pull Quote */}
        <div className="mt-20 max-w-3xl mx-auto text-center">
          <blockquote className="relative">
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 text-6xl text-lime/20 font-serif">
              "
            </div>
            <p className="font-display text-xl sm:text-2xl text-foreground italic leading-relaxed">
              We are moving AI from a tool you talk <em className="text-lime">at</em>, to a
              capability you <em className="text-lime">embody</em>. This is the difference
              between a co-worker and a co-body.
            </p>
          </blockquote>
        </div>
      </div>
    </section>
  );
}
