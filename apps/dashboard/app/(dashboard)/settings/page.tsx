import { createClient } from '@/lib/supabase/server';
import { Settings2, ShieldBan } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function SettingsPage() {
  const supabase = createClient();
  
  const [{ data: config }, { data: blacklist }] = await Promise.all([
    supabase.from('config').select('*').single(),
    supabase.from('blacklist').select('*').order('created_at', { ascending: false }).limit(50)
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-display font-bold text-white mb-2">Settings</h2>
        <p className="text-white/60">Configure pipeline thresholds and manage exclusions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Pipeline Configuration */}
        <div className="glass-card overflow-hidden">
          <div className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
            <Settings2 className="h-5 w-5 text-gold" />
            <h3 className="font-display font-semibold text-lg text-white">Pipeline Configuration</h3>
          </div>
          <div className="p-6">
            <form className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-1.5">Minimum Score Threshold</label>
                  <input 
                    type="number" 
                    defaultValue={config?.min_score_threshold || 50} 
                    className="input-field bg-white/5" 
                    readOnly
                  />
                  <p className="text-xs text-white/40 mt-1">Leads below this score are skipped.</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-1.5">Daily Send Limit</label>
                  <input 
                    type="number" 
                    defaultValue={config?.daily_send_limit || 30} 
                    className="input-field bg-white/5"
                    readOnly
                  />
                  <p className="text-xs text-white/40 mt-1">Max emails sent per day (Brevo free tier).</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-white/80 mb-1.5">System Prompt</label>
                <textarea 
                  defaultValue={config?.system_prompt || ''} 
                  className="input-field bg-white/5 min-h-[150px] font-mono text-xs"
                  readOnly
                />
              </div>

              <div className="pt-4 border-t border-white/10">
                <button type="button" disabled className="btn-primary opacity-50 cursor-not-allowed">
                  Save Changes (Disabled in Demo)
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Blacklist Management */}
        <div className="glass-card overflow-hidden">
          <div className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
            <ShieldBan className="h-5 w-5 text-red-400" />
            <h3 className="font-display font-semibold text-lg text-white">Global Blacklist</h3>
          </div>
          <div className="p-6">
            <form className="flex gap-3 mb-6">
              <input 
                type="text" 
                placeholder="Domain or email to blacklist..." 
                className="input-field flex-1"
                disabled
              />
              <button type="button" disabled className="btn-destructive opacity-50 cursor-not-allowed">
                Add
              </button>
            </form>

            <div className="border border-white/10 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/5 text-white/60">
                  <tr>
                    <th className="px-4 py-3 font-medium">Domain / Email</th>
                    <th className="px-4 py-3 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {blacklist?.map((item) => (
                    <tr key={item.id}>
                      <td className="px-4 py-3 text-white">{item.domain || item.email}</td>
                      <td className="px-4 py-3 text-white/60">{item.reason || 'Manual addition'}</td>
                    </tr>
                  ))}
                  {(!blacklist || blacklist.length === 0) && (
                    <tr>
                      <td colSpan={2} className="px-4 py-8 text-center text-white/40">
                        Blacklist is empty.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
