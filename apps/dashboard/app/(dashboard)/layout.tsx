'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, Mail, Settings, LogOut, Activity } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createClient();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  const navItems = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Leads', href: '/leads', icon: Users },
    { name: 'Outreach', href: '/outreach', icon: Mail },
    { name: 'Campaigns', href: '/campaigns', icon: Activity },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/10 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-white/10">
          <h1 className="font-display text-2xl font-bold text-gold">MAK Lead Engine</h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                  isActive 
                    ? 'bg-gold/10 text-gold font-medium' 
                    : 'text-white/60 hover:bg-white/5 hover:text-white'
                }`}
              >
                <item.icon className={`h-5 w-5 ${isActive ? 'text-gold' : 'text-white/40'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2.5 rounded-xl text-white/60 hover:bg-white/5 hover:text-red-400 transition-all"
          >
            <LogOut className="h-5 w-5 opacity-70" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
