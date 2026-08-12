import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Github, MessageCircle, Mail, ArrowRight, Twitter, Linkedin } from 'lucide-react';
import { toast } from 'sonner';

gsap.registerPlugin(ScrollTrigger);

const footerLinks = [
  { label: 'GitHub', href: 'https://github.com', icon: Github },
  { label: 'Docs', href: '#', icon: Mail },
  { label: 'Privacy', href: '#', icon: null },
];

const socialLinks = [
  { label: 'Twitter', href: 'https://twitter.com', icon: Twitter },
  { label: 'LinkedIn', href: 'https://linkedin.com', icon: Linkedin },
  { label: 'Discord', href: 'https://discord.com', icon: MessageCircle },
];

export function FooterSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLDivElement>(null);
  const [email, setEmail] = useState('');

  useEffect(() => {
    const section = sectionRef.current;
    const cta = ctaRef.current;
    const footer = footerRef.current;

    if (!section || !cta || !footer) return;

    const ctx = gsap.context(() => {
      // CTA animation
      gsap.fromTo(
        cta,
        { opacity: 0, y: 36 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: cta,
            start: 'top 85%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Footer animation
      gsap.fromTo(
        footer,
        { opacity: 0 },
        {
          opacity: 1,
          duration: 0.6,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: footer,
            start: 'top 95%',
            toggleActions: 'play none none reverse',
          },
        }
      );
    }, section);

    return () => ctx.revert();
  }, []);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      toast.success('Thanks for subscribing! You\'ll receive project updates soon.');
      setEmail('');
    }
  };

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-24 lg:py-32 bg-space"
      style={{ zIndex: 80 }}
    >
      <div className="relative z-10 w-full px-6 lg:px-12">
        <div className="max-w-4xl mx-auto">
          {/* CTA Block */}
          <div ref={ctaRef} className="text-center mb-20">
            <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-foreground mb-8 leading-tight">
              The future isn't something you install.{' '}
              <span className="text-lime">It's something that grows with you.</span>
            </h2>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Button
                size="lg"
                className="bg-lime text-space hover:bg-lime-dark font-semibold rounded-full px-8 group"
                onClick={() => window.open('https://github.com', '_blank')}
              >
                Join the Build
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-white/20 text-foreground hover:bg-white/5 rounded-full px-8"
                onClick={() => window.open('mailto:hello@superinstance.ai', '_blank')}
              >
                <Mail className="w-4 h-4 mr-2" />
                Contact Us
              </Button>
            </div>

            {/* Email Subscribe */}
            <form onSubmit={handleSubscribe} className="max-w-md mx-auto">
              <p className="text-sm text-muted-foreground mb-4">
                Subscribe for project updates
              </p>
              <div className="flex gap-3">
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 bg-space-light border-white/10 text-foreground placeholder:text-muted-foreground rounded-full px-5"
                />
                <Button
                  type="submit"
                  variant="outline"
                  className="border-lime/50 text-lime hover:bg-lime/10 rounded-full px-6"
                >
                  Subscribe
                </Button>
              </div>
            </form>
          </div>

          {/* Footer */}
          <footer
            ref={footerRef}
            className="pt-10 border-t border-white/5"
          >
            <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
              {/* Logo */}
              <div className="flex items-center gap-3">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 72 72"
                  fill="none"
                >
                  <defs>
                    <linearGradient id="footerLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#C8FF2E" />
                      <stop offset="100%" stopColor="#9AE600" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M36 4L64 20V52L36 68L8 52V20L36 4Z"
                    stroke="url(#footerLogoGrad)"
                    strokeWidth="2"
                    fill="none"
                  />
                  <circle cx="36" cy="36" r="4" fill="url(#footerLogoGrad)" />
                </svg>
                <span className="font-display font-bold text-lg text-foreground">
                  SuperInstance
                </span>
              </div>

              {/* Links */}
              <div className="flex items-center gap-6">
                {footerLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    target={link.href.startsWith('http') ? '_blank' : undefined}
                    rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>

              {/* Social */}
              <div className="flex items-center gap-4">
                {socialLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-10 h-10 rounded-full bg-space-light border border-white/10 flex items-center justify-center text-muted-foreground hover:text-lime hover:border-lime/30 transition-all"
                    aria-label={link.label}
                  >
                    <link.icon className="w-4 h-4" />
                  </a>
                ))}
              </div>
            </div>

            {/* Copyright */}
            <div className="mt-10 text-center">
              <p className="font-mono text-xs text-muted-foreground">
                © {new Date().getFullYear()} SuperInstance. All rights reserved.
              </p>
            </div>
          </footer>
        </div>
      </div>
    </section>
  );
}
