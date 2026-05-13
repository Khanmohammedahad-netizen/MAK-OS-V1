import { createClient } from '@/lib/supabase/server';
import Link from 'next/link';
import { Search, Filter, Download } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: { q?: string; status?: string; page?: string };
}) {
  const supabase = createClient();
  const page = parseInt(searchParams.page || '1');
  const limit = 20;
  const offset = (page - 1) * limit;

  let query = supabase
    .from('leads')
    .select('*, scores(final_score)', { count: 'exact' });

  if (searchParams.q) {
    query = query.ilike('business_name', `%${searchParams.q}%`);
  }
  
  if (searchParams.status) {
    query = query.eq('status', searchParams.status);
  }

  const { data: leads, count } = await query
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);

  const totalPages = count ? Math.ceil(count / limit) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-white mb-2">Leads</h2>
          <p className="text-white/60">Manage and track your generated leads.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-ghost flex items-center gap-2 border border-white/10">
            <Filter className="h-4 w-4" /> Filter
          </button>
          <button className="btn-ghost flex items-center gap-2 border border-white/10">
            <Download className="h-4 w-4" /> Export
          </button>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-white/40" />
            <input
              type="text"
              placeholder="Search by business name..."
              className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-gold/50 transition-colors"
              defaultValue={searchParams.q}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-white/5 text-white/60 border-b border-white/10">
              <tr>
                <th className="px-6 py-4 font-medium">Business</th>
                <th className="px-6 py-4 font-medium">Location</th>
                <th className="px-6 py-4 font-medium">Source</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Score</th>
                <th className="px-6 py-4 font-medium">Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {leads?.map((lead) => (
                <tr key={lead.id} className="table-row-hover">
                  <td className="px-6 py-4">
                    <Link href={`/leads/${lead.id}`} className="block">
                      <div className="font-medium text-white">{lead.business_name}</div>
                      <div className="text-white/40 text-xs mt-0.5 truncate max-w-[200px]">
                        {lead.website || lead.email || 'No website'}
                      </div>
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-white/80">{lead.city || lead.country || '-'}</td>
                  <td className="px-6 py-4 text-white/60 capitalize">{lead.source}</td>
                  <td className="px-6 py-4">
                    <span className={`badge badge-${lead.status}`}>{lead.status}</span>
                  </td>
                  <td className="px-6 py-4 text-white/80 font-medium">
                    {lead.scores?.[0]?.final_score ?? '-'}
                  </td>
                  <td className="px-6 py-4 text-white/60">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {(!leads || leads.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-white/40">
                    No leads found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination placeholder */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-white/10 flex items-center justify-between text-sm text-white/60">
            <div>
              Showing <span className="text-white font-medium">{offset + 1}</span> to{' '}
              <span className="text-white font-medium">{Math.min(offset + limit, count || 0)}</span> of{' '}
              <span className="text-white font-medium">{count}</span> results
            </div>
            <div className="flex gap-2">
              <Link
                href={`/leads?page=${page - 1}`}
                className={`px-3 py-1 border border-white/10 rounded hover:bg-white/5 ${page <= 1 ? 'pointer-events-none opacity-50' : ''}`}
              >
                Previous
              </Link>
              <Link
                href={`/leads?page=${page + 1}`}
                className={`px-3 py-1 border border-white/10 rounded hover:bg-white/5 ${page >= totalPages ? 'pointer-events-none opacity-50' : ''}`}
              >
                Next
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
