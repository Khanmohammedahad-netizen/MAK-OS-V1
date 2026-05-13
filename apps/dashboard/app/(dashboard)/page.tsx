import { createClient } from '@/lib/supabase/server';
import { Users, Mail, Percent, Trophy, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function OverviewPage() {
  const supabase = createClient();

  // Fetch basic stats (in a real app, these would be aggregated queries or a view)
  const [{ count: totalLeads }, { count: totalSent }] = await Promise.all([
    supabase.from('leads').select('*', { count: 'exact', head: true }),
    supabase.from('outreach_logs').select('*', { count: 'exact', head: true }).eq('status', 'sent')
  ]);

  // Fetch recent leads
  const { data: recentLeads } = await supabase
    .from('leads')
    .select('*, scores(final_score)')
    .order('created_at', { ascending: false })
    .limit(5);

  // Fetch recent runs
  const { data: recentRuns } = await supabase
    .from('pipeline_runs')
    .select('*')
    .order('started_at', { ascending: false })
    .limit(3);

  const stats = [
    { name: 'Total Leads Scraped', value: totalLeads || 0, icon: Users, color: 'text-blue-400' },
    { name: 'Total Emails Sent', value: totalSent || 0, icon: Mail, color: 'text-green-400' },
    { name: 'Reply Rate', value: '4.2%', icon: Percent, color: 'text-purple-400' }, // Hardcoded for demo
    { name: 'Top Score Today', value: '85', icon: Trophy, color: 'text-gold' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-display font-bold text-white mb-2">Overview</h2>
        <p className="text-white/60">Your lead generation engine at a glance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-white/60">{stat.name}</p>
                <p className="mt-2 text-3xl font-bold text-white">{stat.value}</p>
              </div>
              <div className={`p-3 bg-white/5 rounded-xl ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display font-semibold text-white">Recent Leads</h3>
            <Link href="/leads" className="text-sm text-gold hover:text-gold-light flex items-center gap-1">
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5 text-white/60 border-b border-white/10">
                <tr>
                  <th className="px-6 py-4 font-medium">Business</th>
                  <th className="px-6 py-4 font-medium">Location</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {recentLeads?.map((lead) => (
                  <tr key={lead.id} className="table-row-hover">
                    <td className="px-6 py-4">
                      <Link href={`/leads/${lead.id}`} className="block">
                        <div className="font-medium text-white">{lead.business_name}</div>
                        <div className="text-white/40 text-xs mt-0.5 truncate max-w-[200px]">
                          {lead.website || lead.email || 'No contact info'}
                        </div>
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-white/80">{lead.city || lead.country || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`badge badge-${lead.status}`}>{lead.status}</span>
                    </td>
                    <td className="px-6 py-4 text-white/80">
                      {lead.scores?.[0]?.final_score ?? '-'}
                    </td>
                  </tr>
                ))}
                {(!recentLeads || recentLeads.length === 0) && (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-white/40">
                      No leads found. Run the pipeline to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-6">
          <h3 className="text-xl font-display font-semibold text-white">Recent Pipeline Runs</h3>
          <div className="glass-card p-6 space-y-6">
            {recentRuns?.map((run) => (
              <div key={run.id} className="relative pl-6 border-l-2 border-white/10 last:border-transparent pb-6 last:pb-0">
                <div className={`absolute -left-[9px] top-0 h-4 w-4 rounded-full border-2 border-background ${
                  run.status === 'completed' ? 'bg-green-500' : 
                  run.status === 'running' ? 'bg-blue-500 animate-pulse' : 'bg-red-500'
                }`} />
                <p className="text-sm font-medium text-white capitalize">{run.status}</p>
                <p className="text-xs text-white/40 mt-1">
                  {new Date(run.started_at).toLocaleString()}
                </p>
                {run.metrics && Object.keys(run.metrics).length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-white/5 rounded p-2 text-white/70">
                      <span className="block text-white/40 mb-0.5">Scraped</span>
                      {run.metrics.leads_scraped || 0}
                    </div>
                    <div className="bg-white/5 rounded p-2 text-white/70">
                      <span className="block text-white/40 mb-0.5">Sent</span>
                      {run.metrics.emails_sent || 0}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {(!recentRuns || recentRuns.length === 0) && (
              <div className="text-center text-white/40 py-4 text-sm">
                No runs recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
