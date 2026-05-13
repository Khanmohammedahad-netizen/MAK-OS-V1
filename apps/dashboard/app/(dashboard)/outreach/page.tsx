import { createClient } from '@/lib/supabase/server';
import { Send, AlertCircle, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function OutreachPage() {
  const supabase = createClient();
  
  // Fetch recent outreach logs
  const { data: logs } = await supabase
    .from('outreach_logs')
    .select(`
      *,
      leads (
        business_name,
        email
      )
    `)
    .order('created_at', { ascending: false })
    .limit(50);

  // Simple stats calculation for the UI
  const totalSent = logs?.filter(l => l.status === 'sent').length || 0;
  const totalFailed = logs?.filter(l => l.status === 'failed').length || 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-display font-bold text-white mb-2">Outreach</h2>
        <p className="text-white/60">Monitor email deliveries and communication logs.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="stat-card">
          <div className="flex items-center gap-3 mb-2">
            <Send className="h-5 w-5 text-blue-400" />
            <h3 className="text-white/60 font-medium">Total Sent (Recent)</h3>
          </div>
          <p className="text-3xl font-bold text-white">{totalSent}</p>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <h3 className="text-white/60 font-medium">Failed Attempts</h3>
          </div>
          <p className="text-3xl font-bold text-white">{totalFailed}</p>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle2 className="h-5 w-5 text-green-400" />
            <h3 className="text-white/60 font-medium">Delivery Rate</h3>
          </div>
          <p className="text-3xl font-bold text-white">
            {logs && logs.length > 0 ? Math.round((totalSent / logs.length) * 100) : 0}%
          </p>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <h3 className="font-display font-semibold text-lg text-white">Recent Logs</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-white/5 text-white/60 border-b border-white/10">
              <tr>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 font-medium">Lead</th>
                <th className="px-6 py-4 font-medium">Recipient</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs?.map((log) => (
                <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 text-white/60">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <Link href={`/leads/${log.lead_id}`} className="font-medium text-white hover:text-gold transition-colors">
                      {log.leads?.business_name || 'Unknown Lead'}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-white/80">{log.leads?.email || 'N/A'}</td>
                  <td className="px-6 py-4">
                    <span className={`badge badge-${log.status}`}>{log.status}</span>
                  </td>
                  <td className="px-6 py-4 text-white/60 text-xs font-mono truncate max-w-[200px]">
                    {log.error_message || log.brevo_message_id || '-'}
                  </td>
                </tr>
              ))}
              {(!logs || logs.length === 0) && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-white/40">
                    No outreach logs found.
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
