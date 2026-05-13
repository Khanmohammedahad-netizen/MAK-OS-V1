import { createClient } from '@/lib/supabase/server';
import { notFound } from 'next/navigation';
import { ArrowLeft, Globe, MapPin, Building, Mail, Phone, Calendar } from 'lucide-react';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function LeadDetailsPage({ params }: { params: { id: string } }) {
  const supabase = createClient();
  
  const { data: lead } = await supabase
    .from('leads')
    .select(`
      *,
      enrichment(*),
      audits(*),
      scores(*),
      drafts(*),
      outreach_logs(*)
    `)
    .eq('id', params.id)
    .single();

  if (!lead) {
    notFound();
  }

  const score = lead.scores?.[0];
  const audit = lead.audits?.[0];
  const enrichment = lead.enrichment?.[0];
  const draft = lead.drafts?.[0];
  const logs = lead.outreach_logs || [];

  return (
    <div className="space-y-6">
      <Link href="/leads" className="inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors text-sm">
        <ArrowLeft className="h-4 w-4" /> Back to Leads
      </Link>

      <div className="flex flex-col md:flex-row gap-6 items-start justify-between">
        <div>
          <h2 className="text-3xl font-display font-bold text-white flex items-center gap-3">
            {lead.business_name}
            <span className={`badge badge-${lead.status}`}>{lead.status}</span>
          </h2>
          <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-white/60">
            {lead.website && (
              <a href={lead.website} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:text-gold transition-colors">
                <Globe className="h-4 w-4" /> {new URL(lead.website).hostname}
              </a>
            )}
            {(lead.city || lead.country) && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-4 w-4" /> {[lead.city, lead.country].filter(Boolean).join(', ')}
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <Building className="h-4 w-4" /> Source: <span className="capitalize">{lead.source}</span>
            </span>
          </div>
        </div>
        
        {score && (
          <div className="glass-card px-6 py-4 flex items-center gap-4 text-center">
            <div>
              <p className="text-xs text-white/40 uppercase tracking-wider font-semibold">Lead Score</p>
              <p className="text-3xl font-bold text-gold">{score.final_score}</p>
            </div>
            {score.reasons && (
              <div className="text-left border-l border-white/10 pl-4 text-xs text-white/60 max-w-[200px] hidden sm:block">
                <ul className="list-disc list-inside space-y-1">
                  {(score.reasons as string[]).slice(0, 3).map((r, i) => <li key={i} className="truncate">{r}</li>)}
                  {(score.reasons as string[]).length > 3 && <li>+{score.reasons.length - 3} more</li>}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="glass-card overflow-hidden">
            <div className="border-b border-white/10 px-6 py-4">
              <h3 className="font-display font-semibold text-lg text-white">Contact & Enrichment</h3>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-white/40 mb-1">Email</p>
                  <p className="text-white flex items-center gap-2">
                    <Mail className="h-4 w-4 text-white/40" /> {lead.email || 'Not found'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-white/40 mb-1">Phone</p>
                  <p className="text-white flex items-center gap-2">
                    <Phone className="h-4 w-4 text-white/40" /> {lead.phone || 'Not found'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-white/40 mb-1">OSM ID (Internal)</p>
                  <p className="text-white font-mono text-sm">{lead.osm_id || 'N/A'}</p>
                </div>
              </div>
              
              {enrichment ? (
                <div className="space-y-4 border-l border-white/10 pl-6 hidden sm:block">
                  <div>
                    <p className="text-xs text-white/40 mb-1">Company Number</p>
                    <p className="text-white font-mono text-sm">{enrichment.company_number || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-white/40 mb-1">Incorporation Date</p>
                    <p className="text-white flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-white/40" /> 
                      {enrichment.incorporation_date ? new Date(enrichment.incorporation_date).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-white/40 mb-1">SIC Codes</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {(enrichment.sic_codes as string[])?.map(code => (
                        <span key={code} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-xs text-white/80">{code}</span>
                      )) || 'None'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="border-l border-white/10 pl-6 hidden sm:flex items-center justify-center">
                  <p className="text-sm text-white/40 text-center">No enrichment data<br/>available for this lead.</p>
                </div>
              )}
            </div>
          </div>

          {audit && (
            <div className="glass-card overflow-hidden">
              <div className="border-b border-white/10 px-6 py-4">
                <h3 className="font-display font-semibold text-lg text-white">Website Audit</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                  <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                    <p className="text-xs text-white/40 mb-1">Load Time</p>
                    <p className="text-lg font-medium text-white">{audit.load_time_ms ? `${audit.load_time_ms}ms` : 'N/A'}</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                    <p className="text-xs text-white/40 mb-1">Word Count</p>
                    <p className="text-lg font-medium text-white">{audit.word_count || 0}</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                    <p className="text-xs text-white/40 mb-1">Has Framework</p>
                    <p className="text-lg font-medium text-white">{audit.has_framework ? 'Yes' : 'No'}</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                    <p className="text-xs text-white/40 mb-1">Mobile Responsive</p>
                    <p className="text-lg font-medium text-white">{audit.is_responsive ? 'Yes' : 'No'}</p>
                  </div>
                </div>
                
                <div>
                  <p className="text-xs text-white/40 mb-2">Technologies Detected</p>
                  <div className="flex flex-wrap gap-2">
                    {(audit.technologies as string[])?.map(tech => (
                      <span key={tech} className="px-2.5 py-1 bg-white/10 rounded-full text-xs font-medium text-white/90">{tech}</span>
                    )) || <span className="text-sm text-white/40">None detected</span>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {draft && (
            <div className="glass-card overflow-hidden">
              <div className="border-b border-white/10 px-6 py-4 flex justify-between items-center">
                <h3 className="font-display font-semibold text-lg text-white">Generated Draft</h3>
                <span className={`text-xs px-2 py-1 rounded bg-white/5 border border-white/10 ${draft.is_fallback ? 'text-orange-400' : 'text-blue-400'}`}>
                  {draft.is_fallback ? 'Template Fallback' : 'Gemini AI Gen'}
                </span>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <p className="text-xs text-white/40 mb-1">Subject</p>
                  <p className="text-white font-medium bg-white/5 p-3 rounded-lg border border-white/10">{draft.subject}</p>
                </div>
                <div>
                  <p className="text-xs text-white/40 mb-1">Body</p>
                  <div className="bg-white/5 p-4 rounded-lg border border-white/10 text-white/80 whitespace-pre-wrap text-sm leading-relaxed">
                    {draft.body}
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Right Column: Timeline/Logs */}
        <div className="space-y-6">
          <div className="glass-card overflow-hidden">
            <div className="border-b border-white/10 px-6 py-4">
              <h3 className="font-display font-semibold text-lg text-white">Outreach Logs</h3>
            </div>
            <div className="p-6">
              {logs.length > 0 ? (
                <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-white/10">
                  {logs.map((log: any) => (
                    <div key={log.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                      <div className="flex items-center justify-center w-5 h-5 rounded-full border-2 border-background bg-gold shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10"></div>
                      <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.25rem)] p-3 rounded-lg bg-white/5 border border-white/10">
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs font-semibold capitalize ${log.status === 'sent' ? 'text-green-400' : log.status === 'failed' ? 'text-red-400' : 'text-blue-400'}`}>
                            {log.status}
                          </span>
                          <span className="text-[10px] text-white/40">{new Date(log.created_at).toLocaleDateString()}</span>
                        </div>
                        {log.error_message && (
                          <p className="text-xs text-red-300 mt-1">{log.error_message}</p>
                        )}
                        {log.brevo_message_id && (
                          <p className="text-[10px] text-white/30 font-mono mt-1 truncate" title={log.brevo_message_id}>
                            ID: {log.brevo_message_id}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Mail className="h-8 w-8 text-white/20 mx-auto mb-3" />
                  <p className="text-sm text-white/40">No outreach attempts yet.</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
