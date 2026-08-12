import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowRight, Brain, TrendingUp, Monitor } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const blogPosts = [
  {
    icon: Brain,
    title: 'Why the Supplementary Motor Area is the Best Analogy for On-Device AI',
    excerpt:
      'Exploring the biological inspiration behind Mycelium\'s architecture and how the brain\'s motor planning regions inform our approach to embodied intelligence.',
    date: 'Dec 15, 2024',
    readTime: '8 min read',
  },
  {
    icon: TrendingUp,
    title: 'The Economic Case for Swarm Architectures',
    excerpt:
      'Analyzing the cost-inefficiency of monolithic models and making the data-driven case for tiny, specialized agents running in parallel.',
    date: 'Dec 8, 2024',
    readTime: '6 min read',
  },
  {
    icon: Monitor,
    title: 'Beyond the Chatbot: Redefining the OS',
    excerpt:
      'A visionary look at how swarm-based AI architectures could fundamentally replace the traditional operating system paradigm.',
    date: 'Nov 28, 2024',
    readTime: '10 min read',
  },
];

export function BlogSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<(HTMLElement | null)[]>([]);

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
          { opacity: 0, y: 40 },
          {
            opacity: 1,
            y: 0,
            duration: 0.6,
            delay: i * 0.1,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: card,
              start: 'top 85%',
              toggleActions: 'play none none reverse',
            },
          }
        );
      });
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="blog"
      className="relative w-full py-24 lg:py-32 bg-space"
      style={{ zIndex: 70 }}
    >
      <div className="relative z-10 w-full px-6 lg:px-12">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div ref={headerRef} className="flex flex-col sm:flex-row sm:items-end sm:justify-between mb-12">
            <div>
              <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-foreground mb-4">
                Notes on the <span className="text-lime">New Paradigm</span>
              </h2>
              <p className="text-muted-foreground max-w-xl">
                Thoughts on embodied intelligence, swarm architectures, and the future of computing.
              </p>
            </div>
            <button className="mt-6 sm:mt-0 flex items-center gap-2 text-lime hover:text-lime-light transition-colors group">
              <span className="text-sm font-medium">View all posts</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* Blog Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {blogPosts.map((post, i) => (
              <article
                key={post.title}
                ref={(el) => { cardsRef.current[i] = el; }}
                className="group relative bg-space-light rounded-2xl p-6 border border-white/5 hover:border-lime/30 transition-all duration-500 cursor-pointer"
              >
                {/* Icon */}
                <div className="w-12 h-12 rounded-xl bg-lime/10 flex items-center justify-center mb-5 group-hover:bg-lime/20 transition-colors">
                  <post.icon className="w-6 h-6 text-lime" />
                </div>

                {/* Meta */}
                <div className="flex items-center gap-3 mb-3">
                  <span className="font-mono text-xs text-muted-foreground">{post.date}</span>
                  <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                  <span className="font-mono text-xs text-muted-foreground">{post.readTime}</span>
                </div>

                {/* Title */}
                <h3 className="font-display font-semibold text-lg text-foreground mb-3 group-hover:text-lime transition-colors line-clamp-2">
                  {post.title}
                </h3>

                {/* Excerpt */}
                <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
                  {post.excerpt}
                </p>

                {/* Read more */}
                <div className="mt-5 flex items-center gap-2 text-lime opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-sm font-medium">Read more</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
