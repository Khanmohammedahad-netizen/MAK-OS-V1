import { createClient } from '@/lib/supabase/server';
import { Activity, Clock, Play } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function CampaignsPage() {
  const supabase = createClient();
  
  const { data: runs } = await supabase
    .from('pipeline_runs')
    .select('*')
    .order('started_at', { ascending: false })
    .limit(20);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-display font-bold text-white mb-2">Campaigns & Runs</h2>
          <p className="text-white/60">History of automated pipeline executions.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" disabled>
          <Play className="h-4 w-4" /> Trigger Pipeline (Demo)
        </button>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-white/5 text-white/60 border-b border-white/10">
              <tr>
                <th className="px-6 py-4 font-medium">Run ID</th>
                <th className="px-6 py-4 font-medium">Started At</th>
                <th className="px-6 py-4 font-medium">Completed At</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Leads Scraped</th>
                <th className="px-6 py-4 font-medium">Emails Sent</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {runs?.map((run) => (
                <tr key={run.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-white/60">
                    {run.id.split('-')[0]}...
                  </td>
                  <td className="px-6 py-4 text-white flex items-center gap-2">
                    <Clock className="h-4 w-4 text-white/40" />
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-white/60">
                    {run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      run.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                      run.status === 'running' ? 'bg-blue-500/20 text-blue-300 animate-pulse' :
                      'bg-red-500/20 text-red-300'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-white font-medium">
                    {run.metrics?.leads_scraped || 0}
                  </td>
                  <td className="px-6 py-4 text-white font-medium">
                    {run.metrics?.emails_sent || 0}
                  </td>
                </tr>
              ))}
              {(!runs || runs.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-white/40">
                    <Activity className="h-8 w-8 text-white/20 mx-auto mb-3" />
                    <p>No pipeline runs recorded yet.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
